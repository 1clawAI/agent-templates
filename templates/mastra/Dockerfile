FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json tsconfig.json ./
RUN npm install --omit=dev 2>/dev/null || npm install

RUN npm install -g @1claw/mcp@latest 2>/dev/null || \
    echo "WARN: @1claw/mcp install deferred to runtime"

COPY agent.ts .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p /run/1claw

ENV NODE_ENV=production
ENV ONECLAW_DAEMON_SOCKET=/run/1claw/daemon.sock
ENV ONECLAW_FRAMEWORK=mastra

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD curl -sf http://localhost:3000/health || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["./entrypoint.sh"]
