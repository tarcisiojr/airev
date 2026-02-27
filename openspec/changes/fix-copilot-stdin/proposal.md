## Why

O `CopilotCLIRunner` passa o prompt completo como argumento de linha de comando (`-p prompt`). Quando a change analisada é grande, o prompt (diff + contexto + referências + schema) excede o limite `ARG_MAX` do SO (~256KB no macOS), causando `[Errno 7] Argument list too long: 'copilot'`. O runner do Gemini já usa stdin corretamente e não sofre desse problema. A issue #1046 do copilot-cli confirmou que stdin é suportado desde Jan/2026.

## What Changes

- Alterar `CopilotCLIRunner.run()` para passar o prompt via stdin (`input=`) em vez de argumento CLI (`-p`)
- Atualizar testes do runner copilot para refletir a nova forma de invocação
- Atualizar a spec `ai-runner` para refletir que o prompt é passado via stdin

## Capabilities

### New Capabilities

_(nenhuma)_

### Modified Capabilities

- `ai-runner`: O requirement do Runner para Copilot CLI muda para especificar que o prompt é passado via stdin em vez de argumento de linha de comando

## Impact

- **Código**: `src/code_reviewer/runners/copilot.py` — mudança na chamada `subprocess.run`
- **Testes**: `tests/test_copilot_runner.py` — ajuste nos mocks/asserts
- **Specs**: `openspec/specs/ai-runner/spec.md` — atualização do requirement
- **Dependências**: Nenhuma nova dependência. Requer copilot CLI com suporte a stdin (versões recentes, confirmado em Jan/2026)
