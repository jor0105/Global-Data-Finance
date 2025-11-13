import pytest

from src.brazil.dados_b3.historical_quotes.domain.value_objects import (
    ProcessingModeEnum,
)


class TestProcessingModeEnum:
    def test_enum_has_fast_mode(self):
        assert hasattr(ProcessingModeEnum, "FAST")
        assert ProcessingModeEnum.FAST is not None

    def test_enum_has_slow_mode(self):
        assert hasattr(ProcessingModeEnum, "SLOW")
        assert ProcessingModeEnum.SLOW is not None

    def test_fast_mode_value(self):
        assert ProcessingModeEnum.FAST.value == "fast"
        assert ProcessingModeEnum.FAST == "fast"

    def test_slow_mode_value(self):
        assert ProcessingModeEnum.SLOW.value == "slow"
        assert ProcessingModeEnum.SLOW == "slow"

    def test_enum_has_exactly_two_members(self):
        members = list(ProcessingModeEnum)
        assert len(members) == 2

    def test_enum_members_are_strings(self):
        assert isinstance(ProcessingModeEnum.FAST.value, str)
        assert isinstance(ProcessingModeEnum.SLOW.value, str)

    def test_enum_inherits_from_str(self):
        assert isinstance(ProcessingModeEnum.FAST, str)
        assert isinstance(ProcessingModeEnum.SLOW, str)

    def test_can_compare_with_string(self):
        assert ProcessingModeEnum.FAST == "fast"
        assert ProcessingModeEnum.SLOW == "slow"
        assert ProcessingModeEnum.FAST != "slow"
        assert ProcessingModeEnum.SLOW != "fast"

    def test_can_use_in_string_context(self):
        fast_string = f"Mode is {ProcessingModeEnum.FAST}"
        slow_string = f"Mode is {ProcessingModeEnum.SLOW}"
        assert "fast" in fast_string.lower() or "FAST" in fast_string
        assert "slow" in slow_string.lower() or "SLOW" in slow_string

    def test_enum_members_are_unique(self):
        assert ProcessingModeEnum.FAST != ProcessingModeEnum.SLOW

    def test_can_access_by_name(self):
        assert ProcessingModeEnum["FAST"] == ProcessingModeEnum.FAST
        assert ProcessingModeEnum["SLOW"] == ProcessingModeEnum.SLOW

    def test_can_access_by_value(self):
        assert ProcessingModeEnum("fast") == ProcessingModeEnum.FAST
        assert ProcessingModeEnum("slow") == ProcessingModeEnum.SLOW

    def test_invalid_value_raises_error(self):
        with pytest.raises(ValueError):
            ProcessingModeEnum("invalid")

    def test_invalid_name_raises_error(self):
        with pytest.raises(KeyError):
            ProcessingModeEnum["INVALID"]

    def test_enum_iteration(self):
        modes = [mode for mode in ProcessingModeEnum]
        assert len(modes) == 2
        assert ProcessingModeEnum.FAST in modes
        assert ProcessingModeEnum.SLOW in modes

    def test_enum_names_property(self):
        names = [name for name in ProcessingModeEnum.__members__]
        assert "FAST" in names
        assert "SLOW" in names

    def test_enum_values_property(self):
        values = [mode.value for mode in ProcessingModeEnum]
        assert "fast" in values
        assert "slow" in values

    def test_enum_repr(self):
        fast_repr = repr(ProcessingModeEnum.FAST)
        slow_repr = repr(ProcessingModeEnum.SLOW)
        assert "ProcessingModeEnum" in fast_repr or "fast" in fast_repr
        assert "ProcessingModeEnum" in slow_repr or "slow" in slow_repr

    def test_enum_str(self):
        fast_str = str(ProcessingModeEnum.FAST)
        slow_str = str(ProcessingModeEnum.SLOW)
        assert "fast" in fast_str.lower() or fast_str == "fast"
        assert "slow" in slow_str.lower() or slow_str == "slow"

    def test_enum_equality(self):
        assert ProcessingModeEnum.FAST == ProcessingModeEnum.FAST
        assert ProcessingModeEnum.SLOW == ProcessingModeEnum.SLOW
        assert ProcessingModeEnum.FAST != ProcessingModeEnum.SLOW

    def test_enum_identity(self):
        assert ProcessingModeEnum.FAST is ProcessingModeEnum.FAST
        assert ProcessingModeEnum.SLOW is ProcessingModeEnum.SLOW
        assert ProcessingModeEnum.FAST is not ProcessingModeEnum.SLOW

    def test_enum_in_dict_key(self):
        config = {
            ProcessingModeEnum.FAST: {"threads": 8},
            ProcessingModeEnum.SLOW: {"threads": 2},
        }
        assert config[ProcessingModeEnum.FAST]["threads"] == 8
        assert config[ProcessingModeEnum.SLOW]["threads"] == 2

    def test_enum_in_set(self):
        modes_set = {ProcessingModeEnum.FAST, ProcessingModeEnum.SLOW}
        assert len(modes_set) == 2
        assert ProcessingModeEnum.FAST in modes_set
        assert ProcessingModeEnum.SLOW in modes_set

    def test_enum_hashable(self):
        assert hash(ProcessingModeEnum.FAST) is not None
        assert hash(ProcessingModeEnum.SLOW) is not None

    def test_case_sensitive_comparison(self):
        assert ProcessingModeEnum.FAST != "FAST"
        assert ProcessingModeEnum.SLOW != "SLOW"
        assert ProcessingModeEnum.FAST == "fast"
        assert ProcessingModeEnum.SLOW == "slow"
