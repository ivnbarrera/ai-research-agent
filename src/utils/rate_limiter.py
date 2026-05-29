"""Simple rate limiting."""
import asyncio


class RateLimiter:
    """
    Simple semaphore-based rate limiter.

    Limits concurrent operations.
    """

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize rate limiter.

        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        """Acquire semaphore."""
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release semaphore."""
        self.semaphore.release()

    async def execute(self, coro):
        """
        Execute coroutine with rate limiting.

        Args:
            coro: Coroutine to execute

        Returns:
            Result of coroutine
        """
        async with self:
            return await coro


async def _test_rate_limiter():
    """Test rate limiter."""
    import time

    limiter = RateLimiter(max_concurrent=2)

    async def slow_task(n):
        async with limiter:
            print(f"  Task {n} starting")
            await asyncio.sleep(0.5)
            print(f"  Task {n} done")
            return n

    print("Testing with max_concurrent=2...")
    start = time.time()
    results = await asyncio.gather(*[slow_task(i) for i in range(4)])
    elapsed = time.time() - start
    print(f"\n✅ Completed in {elapsed:.2f}s (should be ~1.0s with 2 concurrent)")


if __name__ == "__main__":
    asyncio.run(_test_rate_limiter())
