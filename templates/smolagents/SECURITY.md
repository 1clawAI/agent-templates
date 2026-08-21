# smolagents template security

This template defaults to HuggingFace `ToolCallingAgent`, which only invokes
registered tools. It does **not** execute arbitrary Python.

`CodeAgent` (LLM-generated Python) is available behind
`ONECLAW_SMOLAGENTS_CODE_MODE=1`. Treat that mode as high-trust / development
only:

- Run it only inside the 1Claw spawn container (non-root, network-scoped).
- Do not expose the `/chat` port to the public internet.
- Route LLM traffic through Shroud (`ONECLAW_LLM_VIA_SHROUD=true`).
- Never deploy CodeAgent mode on a host that holds production credentials
  outside the vault.

The 1Claw host injects secrets via the daemon; the container should not
receive raw API keys.
