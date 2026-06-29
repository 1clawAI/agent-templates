#!/bin/sh
set -e

DAEMON_SOCKET="${ONECLAW_DAEMON_SOCKET:-/run/1claw/daemon.sock}"
CHAT_UI_PORT="${CHAT_UI_PORT:-3000}"

echo "─────────────────────────────────────────────"
echo " 1Claw LangChain Agent"
echo "   Framework: langchain"
echo "   Agent ID:  ${ONECLAW_AGENT_ID:-not set}"

if [ -S "$DAEMON_SOCKET" ]; then
    echo "   Mode:      ${ONECLAW_MODE:-cloud} (daemon socket)"
    echo "   Socket:    $DAEMON_SOCKET"
else
    echo "   Mode:      standalone (no daemon socket)"
fi
echo "─────────────────────────────────────────────"

# Route LLM calls through Shroud (transparent to application code)
if [ "$ONECLAW_LLM_VIA_SHROUD" = "true" ]; then
    export OPENAI_BASE_URL="${ONECLAW_SHROUD_URL}/v1"
    echo "LLM routed through Shroud: ${ONECLAW_SHROUD_PROVIDER}/${ONECLAW_SHROUD_MODEL}"
fi

# Start MCP server in background (best-effort)
if [ -S "$DAEMON_SOCKET" ]; then
    if command -v 1claw-mcp >/dev/null 2>&1; then
        ONECLAW_LOCAL_VAULT=true ONECLAW_DAEMON_SOCKET="$DAEMON_SOCKET" \
            1claw-mcp --local 2>/tmp/mcp.log &
        echo "MCP server started in background."
    fi
fi

echo "Ready: http://0.0.0.0:${CHAT_UI_PORT}"
exec python agent.py
