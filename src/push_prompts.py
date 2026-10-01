"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()


PROMPT_KEY = "bug_to_user_story_v2"
INPUT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
INPUT_VARIABLE = "bug_report"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    identifier = f"{username}/{prompt_name}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data["description"]
    if techniques:
        description += f" (técnicas: {', '.join(techniques)})"

    try:
        client = Client()
        url = client.push_prompt(
            identifier,
            object=prompt,
            is_public=True,
            description=description,
            tags=prompt_data.get("tags", []),
        )
    except Exception as e:
        print(f"❌ Erro ao fazer push de '{identifier}': {e}")
        return False

    print(f"✓ Prompt publicado: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    if not prompt_data.get("user_prompt", "").strip():
        errors.append("user_prompt está vazio")

    if f"{{{INPUT_VARIABLE}}}" not in prompt_data.get("user_prompt", ""):
        errors.append(f"user_prompt não contém a variável {{{INPUT_VARIABLE}}}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("Push de prompts para o LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(INPUT_PATH))
    if not data or PROMPT_KEY not in data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {INPUT_PATH.name}")
        return 1
    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    return 0 if push_prompt_to_langsmith(PROMPT_KEY, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
