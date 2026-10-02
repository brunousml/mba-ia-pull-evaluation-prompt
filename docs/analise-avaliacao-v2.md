# Análise da avaliação do prompt v2 e ajustes propostos

Base: 4 execuções do `src/evaluate.py` com o prompt `v2` já publicado, usando o Ollama local (`qwen3.8:27b-mlx`) como gerador e juiz. Foram lidas as notas e os comentários dos juízes (feedback gravado no LangSmith) dos 15 exemplos em cada execução.

## 1. Resultados

| Métrica | Exec. inicial | Rodada 1 | Rodada 2 | Rodada 3 | Média das 3 rodadas |
|---|---|---|---|---|---|
| Helpfulness | 0.81 | 0.82 | 0.81 | 0.81 | **0.813** |
| Correctness | 0.80 | 0.81 | 0.80 | 0.80 | **0.803** |
| F1-Score | 0.80 | 0.80 ✗ | 0.80 | 0.81 | **0.803** |
| Clarity | 0.82 | 0.82 | 0.83 | 0.81 | **0.820** |
| Precision | 0.80 | 0.82 | 0.80 | 0.80 | **0.807** |
| Média geral | 0.8068 | 0.8119 | 0.8090 | 0.8057 | **0.809** |
| Status | aprovado | reprovado (F1 < 0.8) | aprovado | aprovado | |

As médias usam os valores arredondados em duas casas que o script imprime. Nenhuma execução teve `❌ Erro ao avaliar` no log.

**Leitura:** a média passa em todas as métricas, mas com margem de ~0.003 em Correctness e F1. A variação entre rodadas (~0.01) é do mesmo tamanho da margem, então das 4 execuções 3 aprovaram e 1 reprovou. O prompt está na linha de corte.

Como `Correctness` e `Helpfulness` são derivadas (ver `docs/como-funciona-a-avaliacao.md`), o que move a aprovação são as três notas base: **Precision** (entra em 3 das 5 notas), **F1** e **Clarity**.

## 2. Exemplos mais fracos (média das 4 execuções)

| Exemplo | Tipo | F1 | Clarity | Precision |
|---|---|---|---|---|
| Webhook de pagamento não chamado | médio | 0.65 | 0.75 | 0.64 |
| Relatório de vendas lento | médio | 0.67 | 0.79 | 0.68 |
| App offline-first, sincronização | complexo | 0.68 | 0.83 | 0.77 |
| Campo de e-mail sem `@` | simples | 0.80 | 0.79 | 0.77 |
| Imagens no Safari | simples | 0.82 | 0.79 | 0.76 |
| Layout quebrado no iOS landscape | simples | 0.88 | 0.86 | 0.90 |

Os três primeiros concentram a perda de F1. Os simples perdem principalmente em Clarity e Precision.

## 3. Padrões nos comentários dos juízes

### P1. Elaboração além do relato (o mais frequente)

O juiz compara com uma referência enxuta e penaliza tudo que o relato não pediu. Aparece nos três tipos de bug.

- **Simples:** critérios extras como "últimas 2 versões do Safari", "listagem e página individual", "ícones de imagem quebrada", "erro no console", "foco retorna ao campo", "cadastro não deve ser persistido", um segundo cenário com e-mail válido, e frases de efeito ("sem frustração", "com confiança"). O juiz comenta: "elaborações não solicitadas", "sobre-especificação", "A concisão é o ponto mais fraco" (notas de concisão de 0.60 em Clarity).
- **Médio (webhook):** acrescentou "separação, envio", "cliente vê o status na conta", retry com backoff, job de reconciliação e validação de assinatura do payload. O juiz chamou de "alucinação por omissão e adição".
- **Médio (relatório):** acrescentou "índice composto", "geração assíncrona com notificação", "sem truncamento", "time financeiro".

Causa provável no prompt: a regra atual diz "Critérios específicos e testáveis" e permite "sugestão de causa ou correção" no médio, e os exemplos 2 e 3 sugerem solução ("processar de forma assíncrona", "WebSocket"). O modelo imita esse comportamento.

### P2. Persona diferente da esperada

- Webhook: o prompt escreveu "cliente"; a referência usa "sistema de e-commerce". O juiz: "altera a perspectiva ... o que é incorreto".
- Relatório de vendas: "analista comercial" em vez de "gerente de vendas".

O prompt manda "identifique QUEM é afetado", mas não diz como escolher quando há mais de um candidato nem trata bug entre sistemas (webhook, integração, job).

### P3. Meta trocada pelo sintoma

No relatório lento, o relato diz que a geração leva mais de 2 minutos e que o navegador dá timeout em 120 s. O prompt usou "menos de 120 s" como critério, e a referência usa "< 30 s". O juiz: "critério de 120 s no lugar de 30 s, invertendo a exigência". Ou seja, o limite do problema virou meta. O relato não traz meta, então falta uma regra para esse caso.

### P4. Bug complexo: faltam seções e vêm números inventados

Na referência do exemplo complexo (app offline-first) existem as seções `=== TASKS TÉCNICAS SUGERIDAS ===` (4 fases com prazo), `=== MÉTRICAS DE SUCESSO ===` e `=== CONTEXTO DO BUG ===`. O prompt v2 só tem Critérios de Aceitação, Critérios Técnicos e Contexto do Negócio. Comentários repetidos: "faltam ... plano em 4 fases, métricas de sucesso, pausar/retomar sync, backup da versão conflitante, notificar ambos os usuários".

Também há divergência numérica frente à referência ("50" itens por lote e metas de "500/400 MB"):
- O "lote de 100–200 operações" **não está no relato**, então foi inventado pelo modelo, contra a regra "nunca invente dados" já presente no prompt.
- O "limite de 700 MB" **está no relato** (limite do iOS, com 850 MB medidos). A divergência aqui é só com a meta da referência (500/400 MB), que o relato não traz. É o mesmo caso de P3: meta ausente no relato.

### P5. Verbosidade e redundância (Clarity)

Em Clarity, o juiz dá 0.60 para concisão em exemplos simples ("a história repete informação", "frases redundantes: para que eu possa corrigir o erro ... garantir que meu cadastro seja válido e eu consiga receber comunicações"). Organização e ambiguidade ficam em 0.85 a 0.95, então a estrutura está boa. O ganho possível está em encurtar.

## 4. Ajustes propostos para `prompts/bug_to_user_story_v2.yml`

Cada ajuste mira um padrão. São mudanças de texto no system prompt, sem alterar a estrutura nem as variáveis (`{bug_report}` continua só no user prompt). Depois de aplicar, é preciso refazer `python src/push_prompts.py`.

| # | Padrão | Ajuste |
|---|---|---|
| A1 | P1, P5 | Nas regras de comportamento, acrescentar: "Não acrescente critérios, cenários, navegadores, versões ou soluções que o relato não mencione. Cada critério deve ter origem em algo escrito no relato. Prefira poucos critérios, sem frases de efeito no 'para que'." |
| A2 | P1 | Em bugs simples, limitar a **3 a 5 itens** de critério, um cenário só, e sem critério sobre o que o relato não cita (ex.: ícone quebrado, console, versões). |
| A3 | P1 | Em bugs médios, restringir o "Contexto Técnico" a **dados do relato** (endpoint, erro, valores, passos). Sugestão de causa ou correção só quando o relato citar a causa, e em uma linha. Remover do Exemplo 2 a linha "Sugestão: processar de forma assíncrona" ou marcar que ela vem do relato. |
| A4 | P2 | Nova regra de persona: "O perfil do 'Como um' é quem sofre o impacto ou quem é dono do processo citado no relato. Se o relato descreve uma falha entre sistemas (webhook, integração, job) sem usuário final, use o sistema ou o papel que depende dele, e não invente um cliente. Mantenha o cargo que o relato citar (ex.: gerente, analista)." |
| A5 | P3 | Nova regra: "Se o relato dá apenas o valor atual do problema (ex.: demora 2 minutos, timeout de 120 s), não use esse valor como meta. Escreva a meta em termos relativos ('bem abaixo do tempo atual') ou nomeie a meta somente se estiver escrita no relato." |
| A6 | P4 | No formato complexo, acrescentar `=== TASKS TÉCNICAS SUGERIDAS ===` (agrupadas em fases, só com o que decorre do relato) e `=== MÉTRICAS DE SUCESSO ===` (antes/depois, usando os números do relato). Ajustar o Exemplo 3 para mostrar as duas seções. |
| A7 | P4 | Reforçar: "Todo número, limite ou prazo que aparecer na saída tem de estar no relato (ex.: não escreva "lotes de 100 operações" se o relato não diz isso). Se for necessário um valor e ele não existir, descreva sem número." |
| A8 | P4 | No complexo, pedir explicitamente para cobrir todos os comportamentos citados em cada problema (pausar/retomar, backup da versão em conflito, notificar todos os envolvidos), já que a regra de cobertura atual diz só "cada problema". |

**Prioridade sugerida:** A1, A2, A3 e A4 primeiro. Eles atacam P1 e P2, que aparecem em 6 dos 15 exemplos e puxam Precision e F1, as notas de menor margem. Depois A5 a A8, voltados aos exemplos médio (relatório) e complexo.

## 5. Riscos e limites desta análise

- **Referência única.** O juiz pontua contra uma resposta esperada por exemplo. Alguns ajustes (A4, A5) se aproximam do estilo dessas referências e podem não ser a melhor User Story em si. A justificativa aqui é a regra geral (não inventar, coerência com o relato), e não copiar o dataset. Não se deve inserir trechos das referências no prompt.
- **Trade-off de recall.** Reduzir a elaboração (A1 a A3) sobe Precision e Clarity, mas pode baixar F1 se a referência incluir itens que o relato só sugere. Medir de novo é obrigatório.
- **Juiz local ruidoso.** A variação entre rodadas é de ~0.01. Para comparar v2 antes e depois, rodar 3 vezes cada e comparar as médias, sem decidir por uma única execução.
- **Ordem dos exemplos.** O LangSmith lista os exemplos em ordem diferente do log do terminal. Os nomes da seção 2 vêm do conteúdo do relato, não do índice impresso.

## 6. Próximos passos

1. Aplicar A1 a A4 no `v2.yml`, fazer push, rodar 3 avaliações e comparar com a média 0.809 acima.
2. Se F1 ou Precision ficarem abaixo de 0.82 de média, aplicar A5 a A8 e repetir.
3. Registrar no README a comparação v1 vs v2 (e a versão final) e os links dos experimentos.
