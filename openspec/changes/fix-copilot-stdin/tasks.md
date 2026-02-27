## 1. Implementação do Runner

- [x] 1.1 Alterar `CopilotCLIRunner.run()` em `src/code_reviewer/runners/copilot.py` para passar o prompt via `input=prompt` no `subprocess.run`, removendo `-p` e `prompt` da lista de argumentos

## 2. Testes

- [x] 2.1 Atualizar testes em `tests/test_copilot_runner.py` para validar que o prompt é passado via stdin (`input=`) e não como argumento CLI
- [x] 2.2 Adicionar cenário de teste para prompt grande (verificar que não há erro de ARG_MAX)

## 3. Spec

- [x] 3.1 Sincronizar delta spec `ai-runner` com a spec principal em `openspec/specs/ai-runner/spec.md`
