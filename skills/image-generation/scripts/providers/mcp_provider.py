"""Generators reachable only through an MCP server.

A CLI process cannot call an MCP tool: the connection belongs to the agent
session. Rather than pretend otherwise, these providers fail with the exact
handoff instruction, so the caller switches to the MCP tool instead of
debugging a transport that was never going to exist.
"""
from __future__ import annotations

from .base import Provider, ProviderError, Request, Result, register

HANDOFF = {
    "higgsfield": (
        "higgsfield renders through its MCP server, not over HTTP from this CLI. "
        "Call the higgsfield MCP tools from the agent session, then pass the saved "
        "file back here with --ref if it has to seed an OpenAI or Gemini render."
    ),
}


class McpBackedProvider:
    default_model = ""
    key_env = ""

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, request: Request) -> Result:
        raise ProviderError(HANDOFF[self.name])


for provider_name in HANDOFF:
    register(provider_name, (lambda captured: lambda: McpBackedProvider(captured))(provider_name))
