#!/bin/sh
# Start the framework agent on AGENT_INTERNAL_PORT, then run the shared chat UI
# on CHAT_UI_PORT (spawn publishes this port to localhost).
set -e

AGENT_INTERNAL_PORT="${AGENT_INTERNAL_PORT:-3001}"
CHAT_UI_PORT="${CHAT_UI_PORT:-3000}"
export AGENT_INTERNAL_PORT CHAT_UI_PORT

if [ $# -lt 1 ]; then
    echo "Usage: start-with-chat-ui.sh <agent command...>" >&2
    exit 1
fi

"$@" &
AGENT_PID=$!

cleanup() {
    kill "$AGENT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

i=0
while [ "$i" -lt 30 ]; do
    if curl -sf "http://127.0.0.1:${AGENT_INTERNAL_PORT}/health" >/dev/null 2>&1; then
        break
    fi
    i=$((i + 1))
    sleep 0.5
done

echo "Ready: http://0.0.0.0:${CHAT_UI_PORT} (chat UI → agent on :${AGENT_INTERNAL_PORT})"
exec python3 /app/shared/spawn_chat_ui.py
