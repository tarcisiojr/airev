## MODIFIED Requirements

### Requirement: Runner para Copilot CLI
O sistema SHALL implementar `CopilotCLIRunner` que executa o prompt via Copilot CLI, suportando duas formas de instalação:
1. Comando `copilot` standalone (GitHub Copilot CLI)
2. Comando `gh copilot` (extensão do GitHub CLI)

O runner SHALL verificar disponibilidade na ordem: `copilot` standalone primeiro, depois `gh copilot` como fallback.

#### Scenario: Execução com copilot standalone
- **WHEN** o comando `copilot` está disponível no PATH
- **THEN** o runner usa `copilot` para executar o prompt e retorna o output

#### Scenario: Execução com gh copilot (fallback)
- **WHEN** o comando `copilot` não está disponível, mas `gh` com extensão Copilot está instalado
- **THEN** o runner usa `gh copilot` para executar o prompt e retorna o output

#### Scenario: Nenhum Copilot CLI instalado
- **WHEN** nem `copilot` standalone nem `gh copilot` estão disponíveis
- **THEN** o runner lança erro com mensagem listando ambas as opções de instalação
