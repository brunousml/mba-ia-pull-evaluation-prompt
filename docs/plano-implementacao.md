# Plano de implementação (alinhado ao README)

Legenda: ✅ feito · ⏳ pendente

A numeração dos requisitos segue o README (seção "Requisitos"). Ordem de execução do README: pull, refatorar o prompt, push, avaliar.

## Regras do enunciado

- **Não alterar:** `src/evaluate.py`, `src/metrics.py`, `src/utils.py` e `datasets/bug_to_user_story.jsonl`. A única fonte de ajuste das notas é o `prompts/bug_to_user_story_v2.yml` (e a escolha de modelos no `.env`).
- **Implementar:** `prompts/bug_to_user_story_v2.yml`, `src/pull_prompts.py`, `src/push_prompts.py`, `tests/test_prompts.py` e o `README.md`.
- **Estrutura do repositório:** `.env.example`, `requirements.txt`, `README.md`, `prompts/`, `datasets/`, `src/`, `tests/`. Tudo o que está fora disso fica no `.gitignore` (já inclui `screenshots/`, `.idea/`, `.claude/`, `.env` e `venv/`), com exceção de `docs/`, que é versionada como documentação de apoio.
- **Entrega:** repositório público no GitHub (fork do repositório base).
- **Aprovação:** as 5 métricas ≥ 0.8, **cada uma**, e a média ≥ 0.8.
- **Modelos:** o desafio não fixa modelos. Aqui o plano é manter tudo no plano free do Gemini.

## Setup de ambiente ✅

- ✅ Virtualenv `venv/` e dependências do `requirements.txt` instaladas (Python 3.14).
- ✅ `.env` criado a partir do `.env.example`: provider `google`, `LLM_MODEL` e `EVAL_MODEL` em `gemini-3.5-flash-lite`, e `GOOGLE_API_KEY`, `LANGSMITH_API_KEY` e `USERNAME_LANGSMITH_HUB` preenchidos. `OPENAI_API_KEY` fica vazia, sem problema com o provider `google`.
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

## Requisito 4: iteração ⏳

- ⏳ Rodar `python src/evaluate.py`: cada execução cria um experimento no dataset `{LANGSMITH_PROJECT}-eval`, com as 5 notas gravadas como feedback.
- ⏳ Repetir de 3 a 5 iterações (analisar notas baixas, editar o `v2`, novo push, nova avaliação) até **todas** as métricas ≥ 0.8.
- **Atenção ao Gemini free:** o limite é de poucas requisições por minuto e são 15 exemplos com 3 juízes cada, então espere rate limit e execuções lentas.
- **Risco aberto:** com o Gemini, `response.content` chega como lista de blocos (com um campo `signature`), e o `build_target` do `evaluate.py` a passa direto como `answer`. Pode confundir os juízes e derrubar notas sem relação com o prompt. Como `evaluate.py` não pode ser alterado, primeiro rodar e medir. Se as notas forem afetadas, resolver só pelo lado permitido (prompt, `.env`, escolha de modelo) e documentar no README.

## Requisito 5: testes de validação ⏳

Implementar em `tests/test_prompts.py`, mantendo os nomes do esqueleto. Todos carregam o `v2` e desembrulham a chave:

1. `test_prompt_has_system_prompt`: o campo existe e não está vazio.
2. `test_prompt_has_role_definition`: define uma persona (por exemplo "Você é ... Product Manager").
3. `test_prompt_mentions_format`: exige formato Markdown ou User Story padrão ("Como ... eu quero ... para que").
4. `test_prompt_has_few_shot_examples`: contém exemplos de entrada e saída.
5. `test_prompt_no_todos`: não sobrou nenhum `[TODO]` no texto.
6. `test_minimum_techniques`: `techniques_applied` tem pelo menos 2 itens.

Validar com `pytest tests/test_prompts.py`.

## Entregável ⏳

- ⏳ **README.md** com as três seções exigidas:
  - **A) Técnicas Aplicadas (Fase 2):** técnicas escolhidas, justificativa e exemplos práticos de cada uma.
  - **B) Resultados Finais:** link público do dataset de avaliação, screenshots com as notas ≥ 0.8, e comparação v1 vs v2 (o que mudou e por quê).
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
4. `python src/evaluate.py` ⏳ (iterar de 3 a 5 vezes)
5. `pytest tests/test_prompts.py` ⏳
