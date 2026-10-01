# Como funciona a avaliação

Documenta o que acontece quando se roda `python src/evaluate.py`. Os arquivos envolvidos (`src/evaluate.py`, `src/metrics.py`, `src/utils.py`, `datasets/bug_to_user_story.jsonl`) **não podem ser alterados** no desafio.

## Visão geral

```
datasets/bug_to_user_story.jsonl (15 exemplos)
        │  create_evaluation_dataset
        ▼
Dataset no LangSmith: {LANGSMITH_PROJECT}-eval
        │
        │   client.evaluate(target, data=dataset, evaluators=[evaluate_all_metrics])
        ▼
Para cada exemplo (sequencial, max_concurrency=1):
   1. target: prompt do Hub | LLM_MODEL  ->  {"answer": response.content}
   2. evaluator: 3 chamadas ao EVAL_MODEL (juízes) -> 5 notas
        ▼
Experimento no LangSmith (notas como feedback) + resumo no terminal
```

## Passo a passo

1. **Carrega o dataset local.** Cada linha do `.jsonl` tem `inputs.bug_report` (relato do bug) e `outputs.reference` (User Story esperada).
2. **Cria ou reutiliza o dataset no LangSmith**, chamado `{LANGSMITH_PROJECT}-eval`. Se já existe, não recria.
3. **Puxa o prompt do Hub** (`{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`). A fonte da verdade é o Hub, não o YAML local. Por isso, **depois de editar o `v2.yml` é preciso rodar `push_prompts.py` de novo**, senão a avaliação usa a versão antiga.
4. **Roda o experimento.** Para cada exemplo, o prompt vira uma chain (`prompt | llm`) com o modelo `LLM_MODEL`, e a saída (`response.content`) vira o `answer`.
5. **Avalia cada resposta** com `evaluate_all_metrics`, que chama os juízes (LLM-as-judge, modelo `EVAL_MODEL`) e grava as 5 notas como feedback.
6. **Agrega e decide.** Média de cada métrica nos 15 exemplos e média geral.

## As 5 métricas

Três são notas diretas de juízes (`src/metrics.py`); duas são derivadas delas.

| Métrica | Como é calculada |
|---|---|
| **F1-Score** | O juiz dá `precision` e `recall` (0 a 1). O código calcula `2·P·R / (P+R)`. |
| **Clarity** | O juiz dá a média de 4 critérios: organização, linguagem, ausência de ambiguidade e concisão. |
| **Precision** | O juiz dá a média de 3 critérios: ausência de alucinação, foco e correção factual (vs. referência). |
| **Helpfulness** | `(Clarity + Precision) / 2` |
| **Correctness** | `(F1-Score + Precision) / 2` |

Cada juiz recebe o relato, a resposta gerada e a referência. Consequência prática: **Precision pesa em 3 das 5 notas** (a própria, Helpfulness e Correctness), então é a métrica mais importante para subir.

As métricas `tone`, `acceptance_criteria`, `user_story_format` e `completeness` existem em `metrics.py`, mas **não entram** no `evaluate.py`.

## Critério de aprovação

- **Cada** uma das 5 métricas ≥ 0.8, **e**
- média das 5 ≥ 0.8.

Com resposta vazia, as 5 notas saem 0.0 ("Resposta vazia"). Se um juiz lança exceção, a nota dele vira 0.0 e a execução continua. Isso esconde o problema no resumo, então vale sempre olhar o log.

## Configuração relevante (`.env`)

| Variável | Papel |
|---|---|
| `LLM_PROVIDER` | `openai` ou `google` |
| `LLM_MODEL` | modelo que **gera** as User Stories |
| `EVAL_MODEL` | modelo que **julga** (juízes) |
| `LANGSMITH_PROJECT` | define o nome do dataset (`{projeto}-eval`) |
| `USERNAME_LANGSMITH_HUB` | de onde o prompt v2 é puxado |

Cada exemplo custa 1 chamada de geração e 3 de juízes (60 chamadas ao todo para 15 exemplos), em sequência. Em plano free, espere lentidão e possível rate limit.

## Problema encontrado na primeira execução (Gemini)

**Sintoma:** todas as métricas em 0.00 nos 15 exemplos, com a mensagem repetida
`Erro ao avaliar F1-Score/Clarity/Precision: the JSON object must be str, bytes or bytearray, not list`.

**Causa:** com `gemini-3.5-flash-lite`, o `response.content` chega como **lista de blocos**, e não como string. `metrics.py` passa esse valor direto a `json.loads`, que falha. Os três juízes caem no `except` e devolvem 0.0. O mesmo formato de lista chega ao campo `answer` do `build_target`.

**Por que não dá para corrigir no código:** o formato do retorno vem do `metrics.py` e do `evaluate.py`, que são fixos. As alavancas permitidas são o prompt e a escolha de modelos no `.env`.

**Saída:** usar, ao menos no `EVAL_MODEL` (e preferencialmente também no `LLM_MODEL`), um modelo cujo `content` volte como string. Depois de trocar, rodar de novo e checar que o log não tem `❌ Erro ao avaliar`. Registrar no README o modelo escolhido e o motivo.

## Como interpretar os resultados

- **Terminal:** uma linha por exemplo (`F1`, `Clarity`, `Precision`), tabela das 5 métricas com ✓/✗, média geral e status.
- **LangSmith:** o link do experimento aparece no fim. Lá cada exemplo mostra as 5 notas e o `comment` com o raciocínio do juiz, útil para entender **por que** uma nota foi baixa antes de editar o prompt. Os traces também servem como evidência exigida no README.

## Ciclo de iteração

1. `python src/evaluate.py`
2. Ver as notas baixas e os comentários dos juízes no LangSmith.
3. Editar `prompts/bug_to_user_story_v2.yml`.
4. `python src/push_prompts.py`
5. Repetir até todas ≥ 0.8 (de 3 a 5 iterações).
