# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto que converte relatos de bugs em User Stories. O fluxo é: puxar um prompt ruim (v1) do LangSmith Prompt Hub, otimizá-lo com técnicas de Prompt Engineering (v2), publicar de volta e avaliar com 5 métricas (Helpfulness, Correctness, F1-Score, Clarity e Precision). A aprovação exige **cada** métrica ≥ 0.8 e média ≥ 0.8.

## Estrutura

```
.env.example              # Template das variáveis de ambiente
requirements.txt          # Dependências Python
prompts/
  bug_to_user_story_v1.yml  # Prompt inicial (puxado do Hub)
  bug_to_user_story_v2.yml  # Prompt otimizado
datasets/bug_to_user_story.jsonl  # 15 bugs (5 simples, 7 médios, 3 complexos)
src/
  pull_prompts.py         # Pull do LangSmith
  push_prompts.py         # Push ao LangSmith
  evaluate.py, metrics.py, utils.py  # Avaliação (já vinham prontos)
tests/test_prompts.py     # Testes de validação do prompt v2
docs/                     # Análises e plano de implementação
```

## A) Técnicas Aplicadas (Fase 2)

O prompt v1 era um parágrafo genérico: sem persona, sem formato, sem exemplos, e com `{bug_report}` duplicado no system e no user prompt. O v2 (`prompts/bug_to_user_story_v2.yml`) usa três técnicas.

### 1. Few-shot Learning (obrigatória)

**Por quê:** o dataset tem três níveis de complexidade, cada um com um formato de saída diferente. Descrever esses formatos só com texto deixa muita margem; exemplos mostram o formato exato.

**Como:** três exemplos completos de entrada e saída, um por nível:

- **Simples:** uma frase "Como um..., eu quero..., para que..." e um cenário Dado/Quando/Então.
- **Médio:** o mesmo, mais a seção "Contexto Técnico" (erro registrado, causa provável, correção sugerida).
- **Complexo:** formato com `=== USER STORY PRINCIPAL ===`, critérios por problema, critérios técnicos, contexto do bug, tasks em fases, métricas de sucesso e contexto do negócio.

### 2. Role Prompting

**Por quê:** a persona define o ponto de vista. Uma User Story deve falar da necessidade do usuário, e não do defeito técnico.

**Como:** o prompt abre com "Você é uma Product Manager sênior, com 10 anos de experiência em produtos digitais (e-commerce, SaaS, mobile e ERP)". As regras de comportamento reforçam isso: o perfil do "Como um" é quem sofre o impacto, a meta descreve a necessidade (e não o sintoma) e o benefício vem em uma só ideia.

### 3. Chain of Thought (raciocínio interno)

**Por quê:** o bug precisa ser classificado (simples, médio ou complexo) antes de escolher o formato, e relatos com vários problemas não podem perder nenhum.

**Como:** uma lista de passos que o modelo executa sem mostrar: identificar quem é afetado, a necessidade, o valor, todos os problemas distintos, os dados concretos (números, IDs, endpoints) e a complexidade. A saída traz **somente** a User Story, sem o raciocínio, para não poluir a avaliação.

### Outras decisões

- **System vs User:** instruções, regras e exemplos ficam no system prompt. O user prompt só carrega `{bug_report}`, sem duplicação.
- **Edge cases:** regras explícitas para relatos curtos e vagos (não inventar dados), vários problemas (cobrir todos) e bugs simples (não acrescentar cenários que o relato não cita).
- **Não inventar:** números, versões e métricas só podem vir do relato. Sugestões técnicas são tratadas como recomendações, e não como fatos.

## B) Resultados Finais

### Modelos usados

O desafio não fixa modelos. Foram usados dois juízes diferentes, e as notas **não são comparáveis entre si**:

| Juiz | Modelo | Observação |
|---|---|---|
| Ollama local | `qwen3.8:27b-mlx` (gerador e juiz) | Mais rigoroso: o v2 fica perto de 0.80 |
| Gemini | `gemini-2.5-flash` (gerador e juiz) | Mais brando: o v2 fica perto de 0.93 |

O `gemini-3.5-flash-lite` foi descartado porque devolve `content` como lista de blocos, que o `metrics.py` (que não pode ser alterado) não consegue ler, e todas as notas saíram 0.00. O `gemini-2.5-flash` devolve texto simples e funciona.

### Notas do v2 (prompt atual, `gemini-2.5-flash`)

| Métrica | Rodada 1 | Rodada 2 |
|---|---|---|
| Helpfulness | 0.96 ✓ | 0.95 ✓ |
| Correctness | 0.91 ✓ | 0.91 ✓ |
| F1-Score | 0.85 ✓ | 0.86 ✓ |
| Clarity | 0.95 ✓ | 0.93 ✓ |
| Precision | 0.98 ✓ | 0.96 ✓ |
| **Média** | **0.9295** | **0.9240** |
| Status | ✅ Aprovado | ✅ Aprovado |

**Limitação:** foram planejadas 3 rodadas, mas a terceira falhou por `429 RESOURCE_EXHAUSTED` (limite de gasto mensal do projeto no Google AI Studio). Todas as chamadas dos juízes falharam e o experimento ficou com notas ~0.51 de fallback, que não refletem o prompt. Só as 2 rodadas acima são válidas.

### Histórico de iterações (juiz Ollama)

Com o juiz local, mais rigoroso, o v2 ficou na margem da aprovação, e duas tentativas de melhora pioraram o resultado:

| Versão | Média geral | Resultado |
|---|---|---|
| v2 base (3 rodadas extras + 1ª) | 0.809 | 3 de 4 execuções aprovadas (margem ~0.003) |
| Iteração 1 (ajustes A1 a A4) | 0.816 | Reprovou nas 3: F1 caiu para 0.750 |
| Iteração 2 (A3 relaxado, seções de tasks e métricas) | 0.795 | Reprovou nas 3: Precision caiu para ~0.780 |

A análise dos comentários dos juízes está em `docs/analise-avaliacao-v2.md`. O padrão foi um trade-off entre Precision e Recall: cortar o que o relato não cita sobe a Precision e derruba o F1, e o contrário também vale. O prompt atual (iteração 2) é o que aprova com folga no juiz Gemini; no juiz Ollama a versão mais estável foi a base.

### Comparação v1 × v2

| Aspecto | v1 | v2 |
|---|---|---|
| Persona | "um assistente" genérico | Product Manager sênior |
| Exemplos | nenhum | 3 (simples, médio, complexo) |
| Formato de saída | não definido | um formato por nível de complexidade |
| `{bug_report}` | duplicado em system e user | só no user prompt |
| Regras de comportamento | nenhuma | cobrir todos os problemas, não inventar dados, benefício em uma ideia |
| Raciocínio | não orientado | passos internos, saída só com a User Story |
| Edge cases | não tratados | relatos curtos, vários problemas, bugs simples |

### Evidências no LangSmith

- Dataset de avaliação: `{LANGSMITH_PROJECT}-eval`, com 15 exemplos.
- Experimentos do v2 com Gemini: `0ac5088d-b499-4b49-b815-9f9e4f292f5f` (rodada 1) e `f3b79d64-879e-44c0-8c6f-2a8a4e345ced` (rodada 2).
- Link público do dataset: _a preencher após `share_dataset` (ver "Como Executar")._
- Screenshots das notas: _a adicionar em `screenshots/`._

## C) Como Executar

### Pré-requisitos

- Python 3.10 ou superior
- Conta no [LangSmith](https://smith.langchain.com) com API key e um **handle público** (ver `docs/langsmith-hub-username.md`)
- Uma chave de LLM (Google Gemini ou OpenAI) **ou** o [Ollama](https://ollama.com) instalado

### Instalação

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # e preencha os valores
```

### Configuração do `.env`

Variáveis principais: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (usado também no nome do dataset `{LANGSMITH_PROJECT}-eval`), `USERNAME_LANGSMITH_HUB`, `LLM_PROVIDER` (`google` ou `openai`), `LLM_MODEL` e `EVAL_MODEL`, mais a chave do provider escolhido.

- **Gemini:** use um modelo que devolva `content` como texto (por exemplo `gemini-2.5-flash`). Modelos da família 3.x devolvem lista de blocos e zeram as notas.
- **Ollama:** `LLM_PROVIDER=openai`, `OPENAI_API_KEY=ollama`, `OPENAI_BASE_URL=http://localhost:11434/v1` e `LLM_MODEL`/`EVAL_MODEL` com o nome do `ollama list`. Medido com `qwen3.8:27b-mlx` em um M2 Ultra de 64 GB: ~18 GB de disco e ~21 GB de memória. Com menos memória, use um modelo menor, sabendo que a qualidade como juiz tende a cair.

### Fases

```bash
# 1. Pull do prompt inicial (leonanluppi/bug_to_user_story_v1)
python src/pull_prompts.py

# 2. Edite prompts/bug_to_user_story_v2.yml (já incluso nesta entrega)

# 3. Push do prompt otimizado para {USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2
python src/push_prompts.py

# 4. Avaliação (cria um experimento no LangSmith e imprime o link)
python src/evaluate.py

# 5. Testes de validação do prompt
pytest tests/test_prompts.py
```

O `push_prompts.py` retorna `409 Nothing to commit` se o conteúdo não mudou desde o último push. Não é erro.

### Link público do dataset

```python
from langsmith import Client

print(Client().share_dataset(dataset_name="<seu LANGSMITH_PROJECT>-eval")["url"])
```

Compartilhar expõe **todos** os experimentos do dataset, inclusive os reprovados. Rode uma vez e guarde o endereço, porque o link muda a cada compartilhamento.

### Observação sobre o dataset

O `evaluate.py` mostra `Erro ao parsear JSONL ... line 1 column 2` ao ler `datasets/bug_to_user_story.jsonl`. Não afeta a nota quando o dataset `{LANGSMITH_PROJECT}-eval` já existe no LangSmith com os 15 exemplos. Só atrapalha quem recriar o dataset do zero.
