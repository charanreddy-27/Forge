"""In-memory stand-in for the slice of redis.Redis the JobQueue uses."""

from collections import defaultdict


class FakeRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = defaultdict(list)
        self.hashes: dict[str, dict[str, str]] = defaultdict(dict)

    def lpush(self, name: str, *values: str) -> int:
        for value in values:
            self.lists[name].insert(0, value)
        return len(self.lists[name])

    def brpop(self, keys: str, timeout: int = 0) -> tuple[str, str] | None:
        queue = self.lists[keys]
        if not queue:
            return None  # tests never actually block
        return keys, queue.pop()

    def hset(self, name: str, mapping: dict[str, str]) -> int:
        self.hashes[name].update(mapping)
        return len(mapping)

    def hgetall(self, name: str) -> dict[str, str]:
        return dict(self.hashes.get(name, {}))

    def expire(self, name: str, time: int) -> bool:
        return True  # TTL is irrelevant in-memory

    def close(self) -> None:  # called by app lifespan teardown
        pass
