"""Forge agent layer.

The stateless FastAPI service that hosts the LLM Gateway and, in later phases,
the workflow generator, validator, run monitor, and diagnostician. All state
lives in Postgres/Redis so instances can scale horizontally.
"""

__version__ = "0.1.0"
