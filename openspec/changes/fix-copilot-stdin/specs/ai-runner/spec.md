## MODIFIED Requirements

### Requirement: Runner para Copilot CLI
O sistema SHALL implementar `CopilotCLIRunner` que executa o prompt via `copilot` CLI standalone com flags `--yolo` e `--silent`, passando o prompt via stdin.

#### Scenario: Execução com sucesso
- **WHEN** o `copilot` CLI standalone está instalado e autenticado
- **THEN** o runner executa `copilot --yolo --silent` passando o prompt via stdin e retorna o output completo

#### Scenario: Copilot CLI não instalado
- **WHEN** o comando `copilot` não é encontrado no PATH
- **THEN** o runner lança erro com mensagem: "GitHub Copilot CLI não encontrado. Instale em: https://github.com/github/copilot-cli"

#### Scenario: Prompt grande que excede ARG_MAX
- **WHEN** o prompt tem tamanho superior ao limite de argumentos do SO (~256KB)
- **THEN** o runner executa normalmente via stdin sem erro de tamanho
