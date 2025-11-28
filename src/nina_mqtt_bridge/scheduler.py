"""Simple threaded scheduler to poll NINA endpoints on a cadence."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """A recurring task with a fixed interval in seconds."""

    name: str
    interval: float
    fn: Callable[[], None]
    last_run: float = field(default_factory=lambda: 0.0)


class Scheduler:
    """
    Lightweight scheduler that runs tasks on a shared worker thread.

    This is intentionally minimal; each task is expected to be fast and
    non-blocking. Longer-running work should hand off to dedicated threads.
    """

    def __init__(self) -> None:
        self._tasks: List[ScheduledTask] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def add_task(self, task: ScheduledTask) -> None:
        with self._lock:
            self._tasks.append(task)
            logger.debug("Scheduled task added: %s every %ss", task.name, task.interval)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="scheduler", daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = time.monotonic()
            next_delay = 1.0
            with self._lock:
                for task in self._tasks:
                    due_in = (task.last_run + task.interval) - now
                    if due_in <= 0:
                        self._safe_run(task)
                        task.last_run = time.monotonic()
                        due_in = task.interval
                    next_delay = min(next_delay, max(due_in, 0.05))
            self._stop_event.wait(timeout=next_delay)

    def _safe_run(self, task: ScheduledTask) -> None:
        try:
            task.fn()
        except Exception:  # pragma: no cover - surfaced via logs
            logger.exception("Scheduled task '%s' failed", task.name)
