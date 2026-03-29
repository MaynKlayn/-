from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable


class AsyncActionExecutor:
    def __init__(self, workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=workers)

    def submit(self, action: Callable[[], None], on_done: Callable[[BaseException | None], None]) -> Future:
        future = self._executor.submit(action)

        def _callback(done: Future) -> None:
            error = done.exception()
            on_done(error)

        future.add_done_callback(_callback)
        return future

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
