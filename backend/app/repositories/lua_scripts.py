"""Load the Lua scripts of door 1 once and register them on a Redis client."""

from dataclasses import dataclass
from importlib import resources

from redis.asyncio import Redis
from redis.commands.core import AsyncScript


def _source(name: str) -> str:
    return resources.files("app.repositories").joinpath(f"lua/{name}.lua").read_text()


@dataclass(frozen=True, slots=True)
class DocumentScripts:
    """Every status change goes through one of these (EVALSHA, reloaded after a restart)."""

    create: AsyncScript
    begin_run: AsyncScript
    save_chunk: AsyncScript
    finalize: AsyncScript
    restart_run: AsyncScript
    delete: AsyncScript
    note_failure: AsyncScript

    @classmethod
    def register(cls, redis: Redis) -> "DocumentScripts":
        """Register all scripts on ``redis``."""
        return cls(
            create=redis.register_script(_source("create")),
            begin_run=redis.register_script(_source("begin_run")),
            save_chunk=redis.register_script(_source("save_chunk")),
            finalize=redis.register_script(_source("finalize")),
            restart_run=redis.register_script(_source("restart_run")),
            delete=redis.register_script(_source("delete")),
            note_failure=redis.register_script(_source("note_failure")),
        )
