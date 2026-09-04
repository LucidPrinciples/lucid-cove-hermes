FROM python:3.12-slim
WORKDIR /app
COPY team-page/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ltp_store.py .
COPY kb_retrieve.py .
COPY team-page/jules_nc.py .
COPY team-page/app.py .
COPY team-page/tuner_api.py .
COPY team-page/quantum.py .
COPY team-page/data ./data
COPY team-page/static ./static
ENV LCH_VAULT=/vault
ENV PAPERCLIP_URL=http://127.0.0.1:3100
EXPOSE 3200
# 0.0.0.0 required so lucidcove-caddy (bridge) can reach host:3200 via 172.17.0.1
# (127.0.0.1-only bind caused hermes.cove → 502)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3200"]
