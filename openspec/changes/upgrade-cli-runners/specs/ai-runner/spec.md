## ADDED Requirements

### Requirement: Capacidades agentic habilitadas por padrão
Os runners SHALL habilitar capacidades agentic (auto-approve de tools) para permitir que as ferramentas de IA busquem contexto adicional durante a análise.

#### Scenario: Runner executa com tools habilitadas
- **WHEN** o runner executa uma análise
- **THEN** as ferramentas de leitura de arquivos e busca de contexto estão automaticamente aprovadas

### Requirement: Output limpo para CI/CD
Os runners SHALL produzir output limpo e parseável quando executados em ambiente automatizado, sem prompts interativos ou formatação decorativa.

#### Scenario: Execução em CI
- **WHEN** o runner é executado em pipeline CI/CD
- **THEN** o output contém apenas a resposta da análise sem elementos interativos

## MODIFIED Requirements

### Requirement: Runner para Copilot CLI
O sistema SHALL implementar `CopilotCLIRunner` que executa o prompt via `copilot` CLI standalone com flags `--yolo` e `--silent`.

#### Scenario: Execução com sucesso
- **WHEN** o `copilot` CLI standalone está instalado e autenticado
- **THEN** o runner executa `copilot --yolo --silent` com o prompt e retorna o output completo

#### Scenario: Copilot CLI não instalado
- **WHEN** o comando `copilot` não é encontrado no PATH
- **THEN** o runner lança erro com mensagem: "GitHub Copilot CLI não encontrado. Instale em: https://github.com/github/copilot-cli"

## REMOVED Requirements

### Requirement: Suporte a gh copilot extension
**Reason**: O comando `gh copilot` foi deprecated em Outubro/2025 em favor do `copilot` CLI standalone.
**Migration**: Instalar o `copilot` CLI standalone via `npm install -g @anthropic/copilot-cli` ou via Homebrew/WinGet conforme documentação oficial.
