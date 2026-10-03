"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Prompt v2 já desembrulhado da chave raiz do YAML."""
    return load_prompts(str(PROMPT_PATH))[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        system_prompt = prompt_data.get("system_prompt", "")
        assert system_prompt.strip(), "system_prompt ausente ou vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"]
        assert re.search(r"Você é (um|uma)\b.*Product Manager", system_prompt), \
            "o system_prompt não define a persona ('Você é um ... Product Manager')"

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"]
        assert re.search(r"Como um.*eu quero.*para que", system_prompt, re.DOTALL | re.IGNORECASE), \
            "o system_prompt não exige o formato 'Como um ... eu quero ... para que'"

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"]
        examples = re.findall(r"### Exemplo \d+", system_prompt)
        assert len(examples) >= 2, f"esperado pelo menos 2 exemplos, encontrado {len(examples)}"
        assert "Relato de Bug:" in system_prompt, "exemplos sem a entrada ('Relato de Bug:')"
        assert "User Story:" in system_prompt, "exemplos sem a saída ('User Story:')"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        text = f"{prompt_data['system_prompt']}\n{prompt_data.get('user_prompt', '')}"
        assert not re.search(r"\[TODO\]|\bTODO\b", text), "sobrou um TODO no prompt"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert len(techniques) >= 2, f"esperado pelo menos 2 técnicas, encontrado {len(techniques)}"

    def test_prompt_structure_is_valid(self, prompt_data):
        """Valida a estrutura exigida pelo utils.validate_prompt_structure."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"estrutura inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])