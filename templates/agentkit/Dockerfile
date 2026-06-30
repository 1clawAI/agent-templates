FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p /run/1claw

ENV NODE_ENV=production
ENV ONECLAW_DAEMON_SOCKET=/run/1claw/daemon.sock
ENV ONECLAW_FRAMEWORK=agentkit

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD curl -sf http://localhost:3000/health || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["./entrypoint.sh"]
