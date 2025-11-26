import sys
import time


class SimpleProgressBar:
    """
    A small terminal progress bar.

    - Non-blocking: updates only every ~0.1s to reduce console noise.
    - Safe to instantiate with total=0 (no-op printing).
    """

    def __init__(self, total: int, desc: str = "", width: int = 40):
        self.total = max(0, int(total))
        self.desc = desc
        self.width = int(width)
        self.current = 0
        self._last_print_time = 0.0

        if self.total > 0:
            sys.stdout.write(f"\n{desc}: Starting download of {self.total} files...\n")
            sys.stdout.flush()

    def update(self, amount: int = 1) -> None:
        self.current += int(amount)
        now = time.time()
        if now - self._last_print_time >= 0.1 or self.current >= self.total:
            self._print()
            self._last_print_time = now

    def _print(self) -> None:
        if self.total == 0:
            return
        percent = float(self.current) / float(self.total)
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)
        sys.stdout.write(
            f"\r{self.desc} [{bar}] {self.current}/{self.total} ({percent * 100:.0f}%)"
        )
        sys.stdout.flush()

    def close(self) -> None:
        if self.total > 0:
            self._print()
            sys.stdout.write("\n")
            sys.stdout.flush()
