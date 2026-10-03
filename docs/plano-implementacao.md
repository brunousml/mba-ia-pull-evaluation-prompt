# Plano de implementação (alinhado ao README)

Legenda: ✅ feito · 🔄 em andamento · ⏳ pendente · ❌ falhou

A numeração dos requisitos segue o README (seção "Requisitos"). Ordem de execução do README: pull, refatorar o prompt, push, avaliar.

## Regras do enunciado

- **Não alterar:** `src/evaluate.py`, `src/metrics.py`, `src/utils.py` e `datasets/bug_to_user_story.jsonl`. A única fonte de ajuste das notas é o `prompts/bug_to_user_story_v2.yml` (e a escolha de modelos no `.env`).
- **Implementar:** `prompts/bug_to_user_story_v2.yml`, `src/pull_prompts.py`, `src/push_prompts.py`, `tests/test_prompts.py` e o `README.md`.
- **Estrutura do repositório:** `.env.example`, `requirements.txt`, `README.md`, `prompts/`, `datasets/`, `src/`, `tests/`. Tudo o que está fora disso fica no `.gitignore` (já inclui `screenshots/`, `.idea/`, `.claude/`, `.env` e `venv/`), com exceção de `docs/`, que é versionada como documentação de apoio.
- **Entrega:** repositório público no GitHub (fork do repositório base).
- **Aprovação:** as 5 métricas ≥ 0.8, **cada uma**, e a média ≥ 0.8.
- **Modelos:** o desafio não fixa modelos. O Gemini free foi descartado (ver Requisito 4) e a avaliação usa o Ollama local (`qwen3.8:27b-mlx`).

## Setup de ambiente ✅

- ✅ Virtualenv `venv/` e dependências do `requirements.txt` instaladas (Python 3.14).
- ✅ `.env` criado a partir do `.env.example`. Modo atual: **Ollama local** (`LLM_PROVIDER=openai`, `OPENAI_BASE_URL=http://localhost:11434/v1`, `OPENAI_API_KEY=ollama`, `LLM_MODEL` e `EVAL_MODEL` em `qwen3.8:27b-mlx`). As linhas do Gemini ficaram comentadas com `# [modo Gemini]`, com instrução para voltar no próprio arquivo.
- ✅ Handle do LangSmith Hub criado (passo a passo com screenshots em `docs/langsmith-hub-username.md`).
- ✅ IntelliJ configurado com a venv (SDK Python 3.14, `src/` como source root, `tests/` como testes, pytest).
- ✅ Plugins `claude-hud` (statusline, um item por linha) e `claude-mem` instalados.

## Requisito 1: pull do prompt inicial ✅

- ✅ `src/pull_prompts.py`: `pull_prompts_from_langsmith()` chama `Client().pull_prompt("leonanluppi/bug_to_user_story_v1", dangerously_pull_public_prompt=True)`, extrai os templates das mensagens system e human e grava com `save_yaml` em `prompts/bug_to_user_story_v1.yml`. `main()` valida `LANGSMITH_API_KEY` e devolve 0 ou 1.
- ✅ Decisão: usar o prompt indicado no README (`leonanluppi/...`).
- ✅ Validação: o pull foi executado pelo usuário e o conteúdo (`system_prompt` e `user_prompt`) é idêntico ao `v1.yml` versionado.
- **Efeito colateral:** o `v1.yml` foi reescrito sem os comentários do cabeçalho (só formatação). Para restaurar o original: `git checkout -- prompts/bug_to_user_story_v1.yml`.
- **Estrutura do YAML:** o `v1.yml` aninha os campos sob uma chave (`bug_to_user_story_v1:`). O `v2` segue o mesmo padrão, e push e testes desembrulham `data[chave]`, porque `validate_prompt_structure` espera `system_prompt`, `description`, `version` e `techniques_applied` no nível raiz.

## Requisito 2: otimização do prompt ✅ (README pendente)

- ✅ `prompts/bug_to_user_story_v2.yml` criado:
  - **Técnicas:** Few-shot (obrigatório, 3 exemplos), Role Prompting (Product Manager sênior) e Chain of Thought (raciocínio interno, a saída traz só a User Story).
  - **Requisitos do README:** instruções claras, regras explícitas de comportamento, exemplos de entrada e saída, tratamento de edge cases, e System separado do User (`{bug_report}` só no user prompt, sem duplicação como no v1).
  - **Formato:** segue as referências do dataset. Simples: história + critérios Dado/Quando/Então. Médio: + "Contexto Técnico". Complexo: formato completo.
- ✅ Validação: `validate_prompt_structure` passa, e o template tem só a variável `bug_report`. Uma frase com `TODOS` reprovava (substring `TODO`) e foi reescrita. Smoke test no Gemini com formato correto.
- ⏳ **Documentar no README:** quais técnicas foram escolhidas e por quê (entra na seção "Técnicas Aplicadas (Fase 2)").

## Requisito 3: push ✅ (conferir visibilidade)

- ✅ `src/push_prompts.py`:
  - `validate_prompt(prompt_data)`: reaproveita `validate_prompt_structure` e checa que `{bug_report}` aparece no template.
  - `push_prompt_to_langsmith(prompt_name, prompt_data)`: monta o `ChatPromptTemplate` (system + user) e chama `client.push_prompt(f"{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2", object=..., is_public=True, description=..., tags=...)`, incluindo as técnicas aplicadas nos metadados. Devolve `True` ou `False`.
  - `main()`: valida `LANGSMITH_API_KEY` e `USERNAME_LANGSMITH_HUB`, carrega o YAML, valida e faz o push.
- ✅ `python src/push_prompts.py` executado pelo usuário: prompt publicado em `bug_to_user_story_v2` no Hub.
- ⏳ Conferir no dashboard do LangSmith que o prompt está **público**.

## Requisito 4: iteração 🔄 (1ª rodada aprovada, falta confirmar estabilidade)

- ✅ Funcionamento documentado em `docs/como-funciona-a-avaliacao.md`.
- ❌ **Rodada 1 (Gemini `gemini-3.5-flash-lite`): todas as notas 0.00.** O `response.content` chega como lista de blocos e o `metrics.py` o passa ao `json.loads`, que falha (`the JSON object must be str, bytes or bytearray, not list`). Os 3 juízes caem no `except` e devolvem 0.0. Como `evaluate.py` e `metrics.py` não podem ser alterados, a saída foi trocar de modelo.
- ✅ **Rodada 2 (Ollama `qwen3.8:27b-mlx`, gerador e juiz): APROVADO.** A API compatível com a OpenAI devolve `content` como string, então o problema some. Notas: Helpfulness 0.81, Correctness 0.80, F1 0.80, Clarity 0.82, Precision 0.80, **média 0.8068**. Prompt v2 sem alterações em relação ao push inicial.
- **Configuração:** provider `openai` apontando para o Ollama, via `.env` (ver Setup). Documentada no README e no `.env.example`, com os recursos necessários (~18 GB de disco, ~21 GB de memória).
- ✅ **3 rodadas extras (Ollama):** média das 3 = Helpfulness 0.813, Correctness 0.803, F1 0.803, Clarity 0.820, Precision 0.807, **média geral 0.809**. Rodadas: 0.8119 (reprovada por F1 < 0.8), 0.8090 e 0.8057 (aprovadas). Das 4 execuções, 3 aprovaram. Margem de ~0.003, do tamanho da variação entre rodadas (~0.01).
- ✅ **Análise dos comentários dos juízes e ajustes propostos** em `docs/analise-avaliacao-v2.md`. Padrões: elaboração além do relato, persona diferente da esperada, meta trocada pelo sintoma, bug complexo sem seções de tasks e métricas.
- ❌ **Iteração 1 (ajustes A1 a A4 aplicados, commit `4427df5`): reprovou nas 3 rodadas.** Médias: Helpfulness 0.843, Correctness 0.793, F1 **0.750**, Clarity 0.843, Precision 0.843, média geral 0.816. Precision, Clarity e Helpfulness subiram; F1 caiu 0.053 e levou Correctness abaixo de 0.8. Ganhos em bugs simples e no webhook; perdas de recall nos médios e complexos (sugestões técnicas e seções de prevenção/tasks omitidas). Hipótese: A3 e A1 podaram demais. Detalhes em `docs/analise-avaliacao-v2.md`, seções 6 e 7.
- ✅ **Iteração 2 (commit `4df0a28`): reprovou nas 3 rodadas (Ollama).** Médias aproximadas: Helpfulness ~0.800, Correctness ~0.787, F1 ~0.793, Clarity ~0.813, Precision ~0.780, **média geral 0.795** (rodadas: 0.8035, 0.7923, 0.7890). O F1 se recuperou (0.750 → ~0.793), confirmando que A3 e A1 podaram demais, mas Precision caiu de 0.843 para ~0.780 e anulou os ganhos da iteração 1. Pior que a linha de base (0.809) e que a iteração 1 (0.816). Nenhuma variação do v2 fechou todas as métricas ≥ 0.8 de forma estável; a linha de base (`d13e0de`) é a única que aprovou (2 de 3 rodadas).
- ✅ **Hub:** já contém a versão da iteração 2. O `push_prompts.py` retornou `409 Nothing to commit`, então o conteúdo local e o do Hub são iguais (conferido só por esse retorno).
- ⚠️ **Gemini como juiz:** `gemini-3.5-flash-lite` devolve `content` como lista de blocos (inclui `extras.signature`), e `output_version='v0'` não resolve. `gemini-2.5-flash` devolve string e funciona com o `metrics.py` sem alteração. Testado com uma chamada isolada.
- ✅ **Avaliação só com Gemini (`gemini-2.5-flash` como gerador e juiz), prompt da iteração 2:** via variáveis de ambiente (o `.env` segue apontando para o Ollama).
  - **Rodada 1: aprovada.** Helpfulness 0.96, Correctness 0.91, F1 0.85, Clarity 0.95, Precision 0.98, média **0.9295**. Experimento `0ac5088d-b499-4b49-b815-9f9e4f292f5f`.
  - **Rodada 2: aprovada.** 0.95, 0.91, 0.86, 0.93, 0.96, média **0.9240**. Experimento `f3b79d64-879e-44c0-8c6f-2a8a4e345ced`.
  - **Rodada 3: inválida.** O projeto do Google AI Studio atingiu o **limite de gasto mensal** (`429 RESOURCE_EXHAUSTED`); todas as chamadas dos juízes falharam e as notas ~0.51 são o fallback (média 0.5125). Não reflete o prompt. Experimento `feb6084d-5c71-4a22-a971-c22425ced9da` ficou no dataset com essas notas.
  - **Consequência:** não é possível rodar mais avaliações com Gemini até o limite ser liberado (https://ai.studio/spend). Há 2 rodadas válidas, ambas aprovadas, contra 3 pedidas.
  - O juiz Gemini é bem mais brando que o Ollama (~0.93 contra ~0.80 para o mesmo prompt), então as notas não são comparáveis entre os dois juízes.
- ✅ **Decisão (iteração 3):** não é necessária com o juiz Gemini, porque o prompt da iteração 2 já aprova com folga (média ~0.93). Mantém-se o `v2.yml` atual.
- ⏳ Guardar o link do experimento e screenshots das notas, para o README.
- **Observação:** o log mostra `Erro ao parsear JSONL ... line 1 column 2` na leitura local do `datasets/bug_to_user_story.jsonl` (arquivo que não pode ser alterado). Não afetou a nota, porque o dataset `{LANGSMITH_PROJECT}-eval` já existia no LangSmith com os 15 exemplos. Só atrapalharia quem recriasse o dataset do zero.

## Requisito 5: testes de validação ✅

Implementar em `tests/test_prompts.py`, mantendo os nomes do esqueleto. Todos carregam o `v2` e desembrulham a chave:

1. `test_prompt_has_system_prompt`: o campo existe e não está vazio.
2. `test_prompt_has_role_definition`: define uma persona (por exemplo "Você é ... Product Manager").
3. `test_prompt_mentions_format`: exige formato Markdown ou User Story padrão ("Como ... eu quero ... para que").
4. `test_prompt_has_few_shot_examples`: contém exemplos de entrada e saída.
5. `test_prompt_no_todos`: não sobrou nenhum `[TODO]` no texto.
6. `test_minimum_techniques`: `techniques_applied` tem pelo menos 2 itens.

Validar com `pytest tests/test_prompts.py`.

- ✅ **Implementado** (commit `f854604`): os 6 testes do README, mais `test_prompt_structure_is_valid` (reaproveita `validate_prompt_structure`). Usam uma fixture que carrega o `v2.yml` e desembrulha a chave raiz. `pytest tests/test_prompts.py`: **7 passed**.

## Entregável ⏳

- ⏳ **README.md** com as três seções exigidas:
  - **A) Técnicas Aplicadas (Fase 2):** técnicas escolhidas, justificativa e exemplos práticos de cada uma.
  - **B) Resultados Finais:** link público do dataset de avaliação, screenshots com as notas ≥ 0.8, e comparação v1 vs v2 (o que mudou e por quê). Registrar também por que o Gemini foi trocado pelo Ollama e quais modelos foram usados.
  - **C) Como Executar:** pré-requisitos, dependências e comandos de cada fase.
- ⏳ **Evidências no LangSmith:**
  - Dataset de avaliação com 15 exemplos.
  - Execuções do v2 com notas ≥ 0.8.
  - Tracing detalhado de pelo menos 3 exemplos.
  - Link público gerado com `Client().share_dataset(dataset_name="<LANGSMITH_PROJECT>-eval")["url"]`. Rodar uma vez e guardar o endereço, porque o link muda a cada compartilhamento.
- ⏳ **Repositório público** com todo o código, o `v2.yml` completo e o README atualizado.
- **Cuidado com screenshots:** as imagens do LangSmith mostram e-mail e ID da organização na barra lateral. Recortar ou borrar antes de colocá-las no README, que é público.

## Ordem de execução (README)

1. `python src/pull_prompts.py` ✅
2. Refatorar o `v2.yml` ✅
3. `python src/push_prompts.py` ✅
4. `python src/evaluate.py` 🔄 (1ª rodada com Ollama aprovada, falta confirmar estabilidade)
5. `pytest tests/test_prompts.py` ✅
