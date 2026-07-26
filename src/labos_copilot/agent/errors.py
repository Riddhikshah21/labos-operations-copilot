"""Errors raised by the operations agent."""


class OperationsAgentError(RuntimeError):
    """Base error for operations-agent failures."""


class AgentGroundingError(OperationsAgentError):
    """Raised when generated output is not supported by deterministic evidence."""


class AgentProtocolError(OperationsAgentError):
    """Raised when the agent does not follow the required tool workflow."""
