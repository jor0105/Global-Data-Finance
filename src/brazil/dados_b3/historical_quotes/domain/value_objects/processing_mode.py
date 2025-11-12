from dataclasses import dataclass
from enum import Enum


class ProcessingModeEnum(str, Enum):
    FAST = "fast"
    SLOW = "slow"


@dataclass(frozen=True)
class ProcessingMode:
    """Value object representing a valid processing mode.

    Ensures processing mode is either 'fast' or 'slow'.
    """

    value: str

    def __post_init__(self):
        """Validate processing mode on creation."""
        self._validate()

    def _validate(self) -> None:
        """Validate the processing mode.

        Raises:
            ValueError: If processing mode is invalid
        """
        allowed_modes = {m.value for m in ProcessingModeEnum}

        if isinstance(self.value, ProcessingModeEnum):
            object.__setattr__(self, "value", self.value.value)
            return

        if not isinstance(self.value, str):
            raise ValueError("processing_mode must be a string or ProcessingModeEnum")

        mode_value = self.value.strip().lower()

        if mode_value not in allowed_modes:
            raise ValueError(f"processing_mode must be one of {sorted(allowed_modes)}")

        object.__setattr__(self, "value", mode_value)

    def __str__(self) -> str:
        """Return the mode as string."""
        return self.value

    def is_fast(self) -> bool:
        """Check if mode is fast."""
        return self.value == ProcessingModeEnum.FAST.value

    def is_slow(self) -> bool:
        """Check if mode is slow."""
        return self.value == ProcessingModeEnum.SLOW.value
