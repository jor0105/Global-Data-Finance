import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.application.use_cases import (
    GetAvailableDocsUseCase,
)


class TestGetAvailableDocsUseCase:
    def test_execute_returns_available_docs(self):
        use_case = GetAvailableDocsUseCase()
        result = use_case.execute()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_execute_returns_dict_with_doc_codes(self):
        use_case = GetAvailableDocsUseCase()
        result = use_case.execute()

        # Should contain common document types
        common_docs = ["DFP", "ITR", "FRE"]
        for doc in common_docs:
            assert doc in result

    def test_execute_values_are_strings(self):
        use_case = GetAvailableDocsUseCase()
        result = use_case.execute()

        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_initialization_does_not_raise(self):
        try:
            use_case = GetAvailableDocsUseCase()
            assert use_case is not None
        except Exception as e:
            pytest.fail(f"Initialization raised {type(e).__name__}: {e}")
