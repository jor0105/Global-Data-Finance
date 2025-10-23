"""
Testes para a interface DownloadDocsCVMRepository.

Cobre:
- Abstração da interface
- Métodos abstratos obrigatórios
- Implementações concretas
"""

from abc import ABC
from typing import Dict, List
from unittest.mock import Mock

import pytest

from src.brazil.cvm.fundamental_stocks_data.application import DownloadDocsCVMRepository


class TestDownloadDocsCVMRepositoryInterface:
    """Testes para a interface DownloadDocsCVMRepository."""

    def test_interface_is_abstract(self):
        """Deve ser uma classe abstrata."""
        assert isinstance(DownloadDocsCVMRepository, type)
        # Deve herdar de ABC
        assert issubclass(DownloadDocsCVMRepository, ABC)

    def test_interface_cannot_be_instantiated(self):
        """Não deve ser possível instanciar a interface diretamente."""
        with pytest.raises(TypeError):
            DownloadDocsCVMRepository()

    def test_interface_has_download_docs_method(self):
        """Deve ter o método download_docs."""
        assert hasattr(DownloadDocsCVMRepository, "download_docs")

    def test_download_docs_method_is_abstract(self):
        """O método download_docs deve ser abstrato."""
        # Verificar se o método está marcado como abstractmethod
        assert hasattr(DownloadDocsCVMRepository.download_docs, "__isabstractmethod__")
        assert DownloadDocsCVMRepository.download_docs.__isabstractmethod__

    def test_concrete_implementation_must_implement_download_docs(self):
        """Uma implementação concreta deve implementar download_docs."""

        # Criar uma classe que não implementa o método abstrato
        class IncompleteImplementation(DownloadDocsCVMRepository):
            pass

        # Deve falhar ao instanciar
        with pytest.raises(TypeError):
            IncompleteImplementation()

    def test_concrete_implementation_can_be_instantiated(self):
        """Uma implementação concreta que implementa o método pode ser instanciada."""

        class ConcreteImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                pass

        instance = ConcreteImplementation()
        assert isinstance(instance, DownloadDocsCVMRepository)
        assert isinstance(instance, ConcreteImplementation)

    def test_implementation_respects_method_signature(self):
        """A implementação deve respeitar a assinatura do método."""

        class CorrectImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.last_call_args = (your_path, dict_zip_to_download)

        impl = CorrectImplementation()
        test_path = "/path/to/save"
        test_dict = {"DRE": ["https://example.com/DRE_2020.zip"]}

        impl.download_docs(test_path, test_dict)

        assert impl.last_call_args == (test_path, test_dict)

    def test_implementation_can_override_method(self):
        """Implementações podem sobrescrever o método."""

        class Implementation1(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.behavior = "implementation1"

        class Implementation2(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.behavior = "implementation2"

        impl1 = Implementation1()
        impl2 = Implementation2()

        impl1.download_docs("", {})
        impl2.download_docs("", {})

        assert impl1.behavior == "implementation1"
        assert impl2.behavior == "implementation2"

    def test_multiple_implementations_can_coexist(self):
        """Múltiplas implementações podem coexistir."""

        class ImplementationA(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                return "A"

        class ImplementationB(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                return "B"

        implA = ImplementationA()
        implB = ImplementationB()

        assert isinstance(implA, DownloadDocsCVMRepository)
        assert isinstance(implB, DownloadDocsCVMRepository)
        assert implA.__class__ != implB.__class__

    def test_implementation_accepts_empty_dict(self):
        """Implementação deve aceitar dicionário vazio."""

        class TestImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.received_dict = dict_zip_to_download

        impl = TestImplementation()
        impl.download_docs("/path", {})

        assert impl.received_dict == {}

    def test_implementation_accepts_complex_dict(self):
        """Implementação deve aceitar dicionários complexos."""

        class TestImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.received_dict = dict_zip_to_download

        impl = TestImplementation()
        complex_dict = {
            "DRE": [
                "https://example.com/DRE_2020.zip",
                "https://example.com/DRE_2021.zip",
            ],
            "BPARMS": ["https://example.com/BPARMS_2020.zip"],
            "DMPL": ["https://example.com/DMPL_2022.zip"] * 100,
        }

        impl.download_docs("/path", complex_dict)

        assert impl.received_dict == complex_dict

    def test_implementation_accepts_empty_path(self):
        """Implementação deve aceitar caminho vazio."""

        class TestImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.received_path = your_path

        impl = TestImplementation()
        impl.download_docs("", {})

        assert impl.received_path == ""

    def test_implementation_accepts_complex_path(self):
        """Implementação deve aceitar caminhos complexos."""

        class TestImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.received_path = your_path

        impl = TestImplementation()
        complex_path = "/home/user/Programação/dados_ação/2023/downloads"

        impl.download_docs(complex_path, {})

        assert impl.received_path == complex_path

    def test_method_returns_none(self):
        """O método deve retornar None."""

        class TestImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                return None  # Explicitamente

        impl = TestImplementation()
        result = impl.download_docs("/path", {})

        assert result is None

    def test_implementation_can_have_additional_methods(self):
        """Implementação pode ter métodos adicionais."""

        class ExtendedImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                pass

            def additional_method(self):
                return "additional"

            def another_method(self, param):
                return f"param: {param}"

        impl = ExtendedImplementation()

        assert impl.additional_method() == "additional"
        assert impl.another_method("test") == "param: test"

    def test_implementation_can_have_state(self):
        """Implementação pode manter estado."""

        class StatefulImplementation(DownloadDocsCVMRepository):
            def __init__(self):
                self.state = []

            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                self.state.append((your_path, dict_zip_to_download))

        impl = StatefulImplementation()

        impl.download_docs("/path1", {"DRE": []})
        impl.download_docs("/path2", {"BPARMS": []})

        assert len(impl.state) == 2
        assert impl.state[0] == ("/path1", {"DRE": []})
        assert impl.state[1] == ("/path2", {"BPARMS": []})

    def test_implementation_with_mocking(self):
        """Implementação deve funcionar com mocks."""
        # Criar um mock da interface
        mock_repo = Mock(spec=DownloadDocsCVMRepository)

        # Configurar comportamento
        mock_repo.download_docs.return_value = None

        # Usar o mock
        mock_repo.download_docs("/path", {"DRE": []})

        # Verificar chamada
        mock_repo.download_docs.assert_called_once_with("/path", {"DRE": []})


class TestInterfaceWithRealImplementation:
    """Testes usando uma implementação real simples."""

    def test_simple_implementation_works(self):
        """Uma implementação simples deve funcionar."""

        class SimpleImplementation(DownloadDocsCVMRepository):
            def __init__(self):
                self.downloads = []

            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                for doc_name, urls in dict_zip_to_download.items():
                    for url in urls:
                        self.downloads.append(
                            {"path": your_path, "doc": doc_name, "url": url}
                        )

        impl = SimpleImplementation()

        data = {
            "DRE": ["https://example.com/DRE_2020.zip"],
            "BPARMS": [
                "https://example.com/BPARMS_2020.zip",
                "https://example.com/BPARMS_2021.zip",
            ],
        }

        impl.download_docs("/save/path", data)

        assert len(impl.downloads) == 3
        assert impl.downloads[0]["doc"] == "DRE"
        assert impl.downloads[1]["doc"] == "BPARMS"
        assert impl.downloads[2]["doc"] == "BPARMS"

    def test_implementation_interface_compliance(self):
        """Implementação deve estar em conformidade com a interface."""

        class CompliantImplementation(DownloadDocsCVMRepository):
            def download_docs(
                self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
            ) -> None:
                # Implementação válida
                assert isinstance(your_path, str)
                assert isinstance(dict_zip_to_download, dict)

        impl = CompliantImplementation()

        # Chamadas válidas
        impl.download_docs("/path", {})
        impl.download_docs("/path", {"DRE": []})
        impl.download_docs("", {"DRE": ["url"]})
