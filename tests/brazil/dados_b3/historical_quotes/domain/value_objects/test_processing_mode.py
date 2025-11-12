"""Tests for ProcessingModeEnum."""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.value_objects import (
    ProcessingModeEnum,
)


class TestProcessingModeEnum:
    """Test suite for ProcessingModeEnum."""

    def test_enum_has_fast_mode(self):
        """Test that enum has FAST mode."""
        # Act & Assert
        assert hasattr(ProcessingModeEnum, "FAST")
        assert ProcessingModeEnum.FAST is not None

    def test_enum_has_slow_mode(self):
        """Test that enum has SLOW mode."""
        # Act & Assert
        assert hasattr(ProcessingModeEnum, "SLOW")
        assert ProcessingModeEnum.SLOW is not None

    def test_fast_mode_value(self):
        """Test that FAST mode has correct value."""
        # Act & Assert
        assert ProcessingModeEnum.FAST.value == "fast"
        assert ProcessingModeEnum.FAST == "fast"

    def test_slow_mode_value(self):
        """Test that SLOW mode has correct value."""
        # Act & Assert
        assert ProcessingModeEnum.SLOW.value == "slow"
        assert ProcessingModeEnum.SLOW == "slow"

    def test_enum_has_exactly_two_members(self):
        """Test that enum has exactly two members."""
        # Act
        members = list(ProcessingModeEnum)

        # Assert
        assert len(members) == 2

    def test_enum_members_are_strings(self):
        """Test that enum members are strings."""
        # Act & Assert
        assert isinstance(ProcessingModeEnum.FAST.value, str)
        assert isinstance(ProcessingModeEnum.SLOW.value, str)

    def test_enum_inherits_from_str(self):
        """Test that enum inherits from str."""
        # Act & Assert
        assert isinstance(ProcessingModeEnum.FAST, str)
        assert isinstance(ProcessingModeEnum.SLOW, str)

    def test_can_compare_with_string(self):
        """Test that enum members can be compared with strings."""
        # Act & Assert
        assert ProcessingModeEnum.FAST == "fast"
        assert ProcessingModeEnum.SLOW == "slow"
        assert ProcessingModeEnum.FAST != "slow"
        assert ProcessingModeEnum.SLOW != "fast"

    def test_can_use_in_string_context(self):
        """Test that enum members can be used in string context."""
        # Act
        fast_string = f"Mode is {ProcessingModeEnum.FAST}"
        slow_string = f"Mode is {ProcessingModeEnum.SLOW}"

        # Assert
        # When using f-string with Enum, it shows either the value or repr
        assert "fast" in fast_string.lower() or "FAST" in fast_string
        assert "slow" in slow_string.lower() or "SLOW" in slow_string

    def test_enum_members_are_unique(self):
        """Test that enum members have unique values."""
        # Act & Assert
        assert ProcessingModeEnum.FAST != ProcessingModeEnum.SLOW

    def test_can_access_by_name(self):
        """Test that enum members can be accessed by name."""
        # Act & Assert
        assert ProcessingModeEnum["FAST"] == ProcessingModeEnum.FAST
        assert ProcessingModeEnum["SLOW"] == ProcessingModeEnum.SLOW

    def test_can_access_by_value(self):
        """Test that enum members can be accessed by value."""
        # Act & Assert
        assert ProcessingModeEnum("fast") == ProcessingModeEnum.FAST
        assert ProcessingModeEnum("slow") == ProcessingModeEnum.SLOW

    def test_invalid_value_raises_error(self):
        """Test that invalid value raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            ProcessingModeEnum("invalid")

    def test_invalid_name_raises_error(self):
        """Test that invalid name raises KeyError."""
        # Act & Assert
        with pytest.raises(KeyError):
            ProcessingModeEnum["INVALID"]

    def test_enum_iteration(self):
        """Test that enum can be iterated."""
        # Act
        modes = [mode for mode in ProcessingModeEnum]

        # Assert
        assert len(modes) == 2
        assert ProcessingModeEnum.FAST in modes
        assert ProcessingModeEnum.SLOW in modes

    def test_enum_names_property(self):
        """Test that enum has names property."""
        # Act
        names = [name for name in ProcessingModeEnum.__members__]

        # Assert
        assert "FAST" in names
        assert "SLOW" in names

    def test_enum_values_property(self):
        """Test that enum members have correct values."""
        # Act
        values = [mode.value for mode in ProcessingModeEnum]

        # Assert
        assert "fast" in values
        assert "slow" in values

    def test_enum_repr(self):
        """Test string representation of enum members."""
        # Act
        fast_repr = repr(ProcessingModeEnum.FAST)
        slow_repr = repr(ProcessingModeEnum.SLOW)

        # Assert
        assert "ProcessingModeEnum" in fast_repr or "fast" in fast_repr
        assert "ProcessingModeEnum" in slow_repr or "slow" in slow_repr

    def test_enum_str(self):
        """Test string conversion of enum members."""
        # Act
        fast_str = str(ProcessingModeEnum.FAST)
        slow_str = str(ProcessingModeEnum.SLOW)

        # Assert
        # Enum str representation can be either "fast" or "ProcessingModeEnum.FAST"
        assert "fast" in fast_str.lower() or fast_str == "fast"
        assert "slow" in slow_str.lower() or slow_str == "slow"

    def test_enum_equality(self):
        """Test equality comparison between enum members."""
        # Act & Assert
        assert ProcessingModeEnum.FAST == ProcessingModeEnum.FAST
        assert ProcessingModeEnum.SLOW == ProcessingModeEnum.SLOW
        assert ProcessingModeEnum.FAST != ProcessingModeEnum.SLOW

    def test_enum_identity(self):
        """Test identity comparison between enum members."""
        # Act & Assert
        assert ProcessingModeEnum.FAST is ProcessingModeEnum.FAST
        assert ProcessingModeEnum.SLOW is ProcessingModeEnum.SLOW
        assert ProcessingModeEnum.FAST is not ProcessingModeEnum.SLOW

    def test_enum_in_dict_key(self):
        """Test that enum members can be used as dict keys."""
        # Arrange
        config = {
            ProcessingModeEnum.FAST: {"threads": 8},
            ProcessingModeEnum.SLOW: {"threads": 2},
        }

        # Act & Assert
        assert config[ProcessingModeEnum.FAST]["threads"] == 8
        assert config[ProcessingModeEnum.SLOW]["threads"] == 2

    def test_enum_in_set(self):
        """Test that enum members can be added to sets."""
        # Arrange
        modes_set = {ProcessingModeEnum.FAST, ProcessingModeEnum.SLOW}

        # Act & Assert
        assert len(modes_set) == 2
        assert ProcessingModeEnum.FAST in modes_set
        assert ProcessingModeEnum.SLOW in modes_set

    def test_enum_hashable(self):
        """Test that enum members are hashable."""
        # Act & Assert
        assert hash(ProcessingModeEnum.FAST) is not None
        assert hash(ProcessingModeEnum.SLOW) is not None

    def test_case_sensitive_comparison(self):
        """Test that value comparison is case sensitive."""
        # Act & Assert
        assert ProcessingModeEnum.FAST != "FAST"
        assert ProcessingModeEnum.SLOW != "SLOW"
        assert ProcessingModeEnum.FAST == "fast"
        assert ProcessingModeEnum.SLOW == "slow"
