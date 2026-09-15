FROM python:3.12-slim
WORKDIR /app
COPY team-page/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ltp_store.py .
COPY kb_retrieve.py .
COPY team-page/jules_nc.py .
COPY team-page/watch_links.py .
COPY team-page/board_actions.py .
COPY team-page/app.py .
COPY team-page/attention.py .
COPY team-page/connect.py .
COPY team-page/souls.py .
COPY team-page/tuner_api.py .
COPY team-page/mirrors.py .
COPY team-page/ltp_settings.py .
COPY team-page/contact.py .
COPY team-page/quantum.py .
COPY team-page/data ./data
COPY team-page/static ./static
COPY pack/souls /pack/souls
ENV LCH_VAULT=/vault
ENV LCH_PACK=/pack
ENV PAPERCLIP_URL=http://127.0.0.1:3100
EXPOSE 3200
# 0.0.0.0 required so lucidcove-caddy (bridge) can reach host:3200 via 172.17.0.1
# (127.0.0.1-only bind 502s when the house is reached by hostname)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3200"]
