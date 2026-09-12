"""Pick an Attention iframe the *browser* can load.

Paperclip and Hermes both bind loopback on the house host. Probing them from
the Team page (host network) works; handing `http://127.0.0.1:3100` to a phone
on a public HTTPS house host does not (wrong host + mixed content).

The iframe URL is always same-origin (`/attn/pc/…` or `/attn/hm/…`). app.py
reverse-proxies those paths to the loopback backends.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse
import json
import re

PREFIX_PC = "/attn/pc"
PREFIX_HM = "/attn/hm"
FRAME_PC = PREFIX_PC + "/"
FRAME_HM_KANBAN = PREFIX_HM + "/kanban"

_HOUSE_EXACT = {
    "/",
    "/app",
    "/work",
    "/tune",
    "/playlists",
    "/tools",
    "/jules",
    "/deeper",
    "/observer",
}

_HOUSE_PREFIXES = (
    "/static/",
    "/observer/",
    "/attn/",
    "/api/attention",
    "/api/team",
    "/api/config",
    "/api/health",
    "/api/links",
    "/api/tools",
    "/api/jules",
    "/api/presence",
    "/api/onboarding",
    "/api/ltp",
    "/api/kb",
    "/api/agents",
    "/api/tuning",
    "/api/mirrors",
    "/api/account",
)

_HOP_REQ = {
    "host",
    "connection",
    "keep-alive",
    "transfer-encoding",
    "te",
    "trailer",
    "upgrade",
    "content-length",
    "proxy-connection",
    # Paperclip 403s on the house hostname even when Host is loopback.
    # Caddy (and the browser Origin) must not reach the backend.
    "x-real-ip",
    "forwarded",
    "origin",
    "cf-connecting-ip",
    "true-client-ip",
    "via",
}

_HOP_RESP = {
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
    "proxy-connection",
    "x-frame-options",
    "content-security-policy",
}


def pick_attention_frame(
    paperclip_ok: bool,
    hermes_ok: bool,
    paperclip_url: str = "",
    hermes_url: str = "",
) -> dict[str, str]:
    """Same-origin iframe. paperclip_url / hermes_url are unused (loopback)."""
    _ = (paperclip_url, hermes_url)
    if paperclip_ok:
        return {"source": "paperclip", "url": FRAME_PC, "title": "Paperclip"}
    if hermes_ok:
        return {"source": "hermes", "url": FRAME_HM_KANBAN, "title": "Hermes Kanban"}
    return {"source": "none", "url": "", "title": "Attention"}


def is_house_reserved(path: str) -> bool:
    p = path or "/"
    if not p.startswith("/"):
        p = "/" + p
    if p in _HOUSE_EXACT:
        return True
    for pref in _HOUSE_PREFIXES:
        trimmed = pref.rstrip("/")
        if pref.endswith("/"):
            if p.startswith(pref):
                return True
        elif p == trimmed or p.startswith(trimmed + "/"):
            return True
    return False


def referer_attn_kind(referer: str) -> str | None:
    if not referer:
        return None
    path = urlparse(referer).path or ""
    if path == PREFIX_PC or path.startswith(PREFIX_PC + "/"):
        return "pc"
    if path == PREFIX_HM or path.startswith(PREFIX_HM + "/"):
        return "hm"
    return None


def strip_proxy_prefix(path: str, prefix: str) -> str:
    """Drop the house iframe prefix so Paperclip never sees /attn/pc as an org."""
    raw = path or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    pref = (prefix or "").rstrip("/")
    if not pref:
        return raw
    if raw == pref or raw == pref + "/":
        return "/"
    if raw.startswith(pref + "/"):
        rest = raw[len(pref) :]
        return rest if rest.startswith("/") else "/" + rest
    return raw


def join_backend(backend: str, path: str) -> str | None:
    """Join path onto backend; reject anything that leaves the backend origin."""
    base = (backend or "").rstrip("/") + "/"
    raw = path or ""
    if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("//"):
        return None
    if not raw.startswith("/"):
        raw = "/" + raw
    for pref in (PREFIX_PC, PREFIX_HM):
        stripped = strip_proxy_prefix(raw, pref)
        if stripped != raw:
            raw = stripped
            break
    raw = raw.lstrip("/")
    target = urljoin(base, raw)
    back = urlparse(base)
    got = urlparse(target)
    if got.scheme != back.scheme or (got.hostname or "").lower() != (back.hostname or "").lower():
        return None
    if back.port != got.port:
        return None
    prefix = base.rstrip("/")
    if not (target == prefix or target.startswith(prefix + "/") or target.startswith(prefix + "?")):
        return None
    return target


def rewrite_location(location: str, backend: str, prefix: str) -> str:
    if not location:
        return location
    backend = backend.rstrip("/")
    prefix = prefix.rstrip("/")
    if location.startswith(backend):
        rest = location[len(backend):]
        if not rest.startswith("/"):
            rest = "/" + rest if rest else "/"
        return prefix + rest
    if location.startswith("/") and not location.startswith("//"):
        return prefix + location
    return location


def rewrite_referer_to_backend(referer: str, prefix: str, backend: str) -> str:
    prefix = prefix.rstrip("/")
    backend = backend.rstrip("/")
    parsed = urlparse(referer or "")
    path = parsed.path or "/"
    if path == prefix:
        path = "/"
    elif path.startswith(prefix + "/"):
        path = path[len(prefix):] or "/"
        if not path.startswith("/"):
            path = "/" + path
    out = backend + path
    if parsed.query:
        out += "?" + parsed.query
    return out


def backend_origin(backend: str) -> str:
    parsed = urlparse(backend)
    return f"{parsed.scheme}://{parsed.netloc}"


def rewrite_set_cookie(value: str) -> str:
    """Drop Domain so the cookie sticks to the house host."""
    return re.sub(r";\s*domain=[^;]*", "", value, flags=re.I)


def _location_shim(prefix: str) -> str:
    """Keep the real iframe URL under /attn/pc (Referer still proxies).

    Paperclip's org router is client-side: first path segment of the iframe
    URL becomes the company prefix, so /attn/pc/ is org ATTN. Location.prototype
    pathname is unforgeable in Chromium, so a getter patch is not enough.
    React Router createBrowserHistory reads history.state.masked first, then
    window.location. Seed masked to / and keep it stripped on push/replace.
    """
    p = json.dumps((prefix or "").rstrip("/") or prefix)
    return (
        "<script>(function(){var p="
        + p
        + ";"
        "function strip(path){if(!path)return path;if(path===p||path===p+'/')return '/';"
        "if(path.indexOf(p+'/')===0)return path.slice(p.length)||'/';return path;}"
        "function add(u){if(u==null||u==='')return u;"
        "try{var x=new URL(u,location.origin+p+'/');"
        "if(x.origin!==location.origin)return u;"
        "if(x.pathname!==p&&x.pathname.indexOf(p+'/')!==0){"
        "x.pathname=p+(x.pathname.charAt(0)==='/'?x.pathname:'/'+x.pathname);}"
        "return x.pathname+x.search+x.hash;}catch(e){return u;}}"
        "function partsFrom(u){try{var x=new URL(u,location.href);"
        "return {pathname:strip(x.pathname),search:x.search,hash:x.hash};}"
        "catch(e){return {pathname:'/',search:'',hash:''};}}"
        "function seed(s,u){var n=s&&typeof s==='object'?Object.assign({},s):{usr:s};"
        "if(typeof u==='string'&&u){n.masked=partsFrom(u);}"
        "else if(n.masked&&n.masked.pathname){"
        "n.masked={pathname:strip(n.masked.pathname),search:n.masked.search||'',hash:n.masked.hash||''};}"
        "else{n.masked={pathname:strip(location.pathname),search:location.search,hash:location.hash};}"
        "if(n.idx==null)n.idx=0;return n;}"
        "try{var d=Object.getOwnPropertyDescriptor(Location.prototype,'pathname');"
        "if(d&&d.get){Object.defineProperty(Location.prototype,'pathname',"
        "{configurable:true,enumerable:true,get:function(){return strip(d.get.call(this));}});}}"
        "catch(e){}"
        "var ps=History.prototype.pushState,rs=History.prototype.replaceState;"
        "History.prototype.pushState=function(s,t,u){if(typeof u==='string')u=add(u);return ps.call(this,seed(s,u),t,u);};"
        "History.prototype.replaceState=function(s,t,u){if(typeof u==='string')u=add(u);return rs.call(this,seed(s,u),t,u);};"
        "try{rs.call(history,seed(history.state,p+'/'),'',location.pathname+location.search+location.hash);}catch(e){}"
        "})();</script>"
    )


def _fetch_shim(prefix: str) -> str:
    # prefix is a house-controlled path (/attn/pc) — not request input.
    return (
        "<script>(function(){var p=\"" + prefix + "\";"
        "function fix(u){if(typeof u!==\"string\")return u;"
        "if(!u||u.charAt(0)===\"#\"||u.slice(0,5)===\"data:\"||u.slice(0,5)===\"blob:\")return u;"
        "if(u.indexOf(p+\"/\")===0||u===p||u===p+\"/\")return u;"
        "if(u.charAt(0)===\"/\"&&u.charAt(1)!==\"/\")return p+u;"
        "try{var x=new URL(u,location.href);"
        "if(x.origin===location.origin&&x.pathname.indexOf(p+\"/\")!==0&&x.pathname!==p)"
        "x.pathname=p+x.pathname;return x.href;}catch(e){return u;}}"
        "var f=window.fetch;window.fetch=function(i,n){"
        "if(typeof i===\"string\")i=fix(i);"
        "else if(i&&typeof Request!==\"undefined\"&&i instanceof Request)i=new Request(fix(i.url),i);"
        "return f.call(this,i,n);};"
        "var o=XMLHttpRequest.prototype.open;"
        "XMLHttpRequest.prototype.open=function(m,u){arguments[1]=fix(u);return o.apply(this,arguments);};"
        "})();</script>"
    )


def rewrite_html(html: str, prefix: str, backend: str) -> str:
    prefix = prefix.rstrip("/")
    backend = backend.rstrip("/")
    inject = f'<base href="{prefix}/">' + _location_shim(prefix) + _fetch_shim(prefix)
    lower = html.lower()
    idx = lower.find("<head")
    if idx >= 0:
        gt = html.find(">", idx)
        if gt >= 0:
            html = html[: gt + 1] + inject + html[gt + 1 :]
        else:
            html = inject + html
    else:
        html = inject + html
    if backend:
        html = html.replace(backend, prefix)
    return html


def hop_skip_request(name: str) -> bool:
    n = name.lower()
    return n in _HOP_REQ or n.startswith("x-forwarded-")


def hop_skip_response(name: str) -> bool:
    return name.lower() in _HOP_RESP


def is_html_content_type(content_type: str) -> bool:
    ct = (content_type or "").lower()
    return "text/html" in ct or "application/xhtml" in ct
