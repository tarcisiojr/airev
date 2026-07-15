# Avaliação de Recall

Suite de casos com bugs conhecidos para medir o recall do airev e detectar
regressão a cada mudança no prompt (`src/code_reviewer/prompts/review_system.md`).

## Estrutura

Cada caso em `cases/<nome>/` contém:

| Item | Descrição |
|------|-----------|
| `before/` | Estado inicial do código (vira a branch `main`) |
| `after/` | Estado com o bug introduzido (vira a branch `feature/eval`) |
| `expected.json` | Findings esperados: arquivo, categoria e faixa de linhas |

## Casos atuais

- `undefined_variable` — typo em nome de variável (NameError em runtime)
- `sql_injection` — query montada com f-string e entrada do usuário
- `command_injection` — comando shell com `shell=True` e entrada do usuário
- `n_plus_one` — query executada dentro de loop
- `resource_leak` — arquivo aberto sem `with`/`close()`

## Execução

Requer um runner de IA instalado (gemini ou copilot). Não faz parte da
suite pytest por depender de chamadas reais de IA.

```bash
# Todos os casos
python evals/run_evals.py

# Um caso específico
python evals/run_evals.py --case sql_injection

# Com outro runner ou modo thorough
python evals/run_evals.py --runner copilot --thorough
```

O script imprime dois números:

- **Recall (detecção)**: o problema foi apontado no arquivo/linhas esperados
- **Recall (categoria correta)**: além de detectado, a categoria bateu

Código de saída: `0` = recall 100%, `2` = houve falha de detecção.

## Adicionando um caso

1. Crie `cases/<nome>/before/` e `cases/<nome>/after/` com o código
2. Descreva os findings esperados em `cases/<nome>/expected.json`
3. Rode `python evals/run_evals.py --case <nome>`
