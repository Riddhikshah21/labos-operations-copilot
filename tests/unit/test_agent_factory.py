from agents.mcp import MCPServerStdio

from labos_copilot.agent.schemas import (
    OperationsNarrative,
)
from labos_copilot.agent.service import (
    create_operations_agent,
)


def test_agent_uses_mcp_and_structured_output() -> None:
    server = MCPServerStdio(
        name="Test MCP Server",
        params={
            "command": "python",
            "args": [],
        },
    )

    agent = create_operations_agent(
        model_name="gpt-5-nano",
        server=server,
    )

    assert agent.model == "gpt-5-nano"
    assert agent.output_type is OperationsNarrative
    assert agent.mcp_servers == [server]
    assert agent.handoffs == []
