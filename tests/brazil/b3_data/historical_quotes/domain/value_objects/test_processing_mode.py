import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.domain.value_objects import (
    ProcessingModeEnumB3,
)


class TestProcessingModeEnumB3:
    def test_enum_has_fast_mode(self):
        assert hasattr(ProcessingModeEnumB3, "FAST")
        assert ProcessingModeEnumB3.FAST is not None

    def test_enum_has_slow_mode(self):
        assert hasattr(ProcessingModeEnumB3, "SLOW")
        assert ProcessingModeEnumB3.SLOW is not None

    def test_fast_mode_value(self):
        assert ProcessingModeEnumB3.FAST.value == "fast"
        assert ProcessingModeEnumB3.FAST == "fast"

    def test_slow_mode_value(self):
        assert ProcessingModeEnumB3.SLOW.value == "slow"
        assert ProcessingModeEnumB3.SLOW == "slow"

    def test_enum_has_main_members(self):
        assert ProcessingModeEnumB3.FAST in ProcessingModeEnumB3
        assert ProcessingModeEnumB3.SLOW in ProcessingModeEnumB3
        # The enum has additional configuration constants as pseudo-members

    def test_enum_members_are_strings(self):
        assert isinstance(ProcessingModeEnumB3.FAST.value, str)
        assert isinstance(ProcessingModeEnumB3.SLOW.value, str)

    def test_enum_inherits_from_str(self):
        assert isinstance(ProcessingModeEnumB3.FAST, str)
        assert isinstance(ProcessingModeEnumB3.SLOW, str)

    def test_can_compare_with_string(self):
        assert ProcessingModeEnumB3.FAST == "fast"
        assert ProcessingModeEnumB3.SLOW == "slow"
        assert ProcessingModeEnumB3.FAST != "slow"
        assert ProcessingModeEnumB3.SLOW != "fast"

    def test_can_use_in_string_context(self):
        fast_string = f"Mode is {ProcessingModeEnumB3.FAST}"
        slow_string = f"Mode is {ProcessingModeEnumB3.SLOW}"
        assert "fast" in fast_string.lower() or "FAST" in fast_string
        assert "slow" in slow_string.lower() or "SLOW" in slow_string

    def test_enum_members_are_unique(self):
        assert ProcessingModeEnumB3.FAST != ProcessingModeEnumB3.SLOW

    def test_can_access_by_name(self):
        assert ProcessingModeEnumB3["FAST"] == ProcessingModeEnumB3.FAST
        assert ProcessingModeEnumB3["SLOW"] == ProcessingModeEnumB3.SLOW

    def test_can_access_by_value(self):
        assert ProcessingModeEnumB3("fast") == ProcessingModeEnumB3.FAST
        assert ProcessingModeEnumB3("slow") == ProcessingModeEnumB3.SLOW

    def test_invalid_value_raises_error(self):
        with pytest.raises(ValueError):
            ProcessingModeEnumB3("invalid")

    def test_invalid_name_raises_error(self):
        with pytest.raises(KeyError):
            ProcessingModeEnumB3["INVALID"]

    def test_enum_iteration(self):
        modes = [
            member
            for member in ProcessingModeEnumB3
            if member in [ProcessingModeEnumB3.FAST, ProcessingModeEnumB3.SLOW]
        ]
        assert len(modes) == 2
        assert ProcessingModeEnumB3.FAST in modes
        assert ProcessingModeEnumB3.SLOW in modes

    def test_enum_names_property(self):
        names = [name for name in ProcessingModeEnumB3.__members__]
        assert "FAST" in names
        assert "SLOW" in names

    def test_enum_values_property(self):
        values = [
            member.value
            for member in ProcessingModeEnumB3
            if member in [ProcessingModeEnumB3.FAST, ProcessingModeEnumB3.SLOW]
        ]
        assert "fast" in values
        assert "slow" in values

    def test_enum_repr(self):
        fast_repr = repr(ProcessingModeEnumB3.FAST)
        slow_repr = repr(ProcessingModeEnumB3.SLOW)
        assert "ProcessingModeEnumB3" in fast_repr or "fast" in fast_repr
        assert "ProcessingModeEnumB3" in slow_repr or "slow" in slow_repr

    def test_enum_str(self):
        fast_str = str(ProcessingModeEnumB3.FAST)
        slow_str = str(ProcessingModeEnumB3.SLOW)
        assert "fast" in fast_str.lower() or fast_str == "fast"
        assert "slow" in slow_str.lower() or slow_str == "slow"

    def test_enum_equality(self):
        assert ProcessingModeEnumB3.FAST == ProcessingModeEnumB3.FAST
        assert ProcessingModeEnumB3.SLOW == ProcessingModeEnumB3.SLOW
        assert ProcessingModeEnumB3.FAST != ProcessingModeEnumB3.SLOW

    def test_enum_identity(self):
        assert ProcessingModeEnumB3.FAST is ProcessingModeEnumB3.FAST
        assert ProcessingModeEnumB3.SLOW is ProcessingModeEnumB3.SLOW
        assert ProcessingModeEnumB3.FAST is not ProcessingModeEnumB3.SLOW

    def test_enum_in_dict_key(self):
        config = {
            ProcessingModeEnumB3.FAST: {"threads": 8},
            ProcessingModeEnumB3.SLOW: {"threads": 2},
        }
        assert config[ProcessingModeEnumB3.FAST]["threads"] == 8
        assert config[ProcessingModeEnumB3.SLOW]["threads"] == 2

    def test_enum_in_set(self):
        modes_set = {ProcessingModeEnumB3.FAST, ProcessingModeEnumB3.SLOW}
        assert len(modes_set) == 2
        assert ProcessingModeEnumB3.FAST in modes_set
        assert ProcessingModeEnumB3.SLOW in modes_set

    def test_enum_hashable(self):
        assert hash(ProcessingModeEnumB3.FAST) is not None
        assert hash(ProcessingModeEnumB3.SLOW) is not None

    def test_case_sensitive_comparison(self):
        assert ProcessingModeEnumB3.FAST != "FAST"
        assert ProcessingModeEnumB3.SLOW != "SLOW"
        assert ProcessingModeEnumB3.FAST == "fast"
        assert ProcessingModeEnumB3.SLOW == "slow"
