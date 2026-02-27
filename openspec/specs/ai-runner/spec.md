## ADDED Requirements

### Requirement: Interface plugável para CLIs de IA
O sistema SHALL definir um Protocol `AIRunner` com método `run(prompt: str, workdir: Path) -> str` que cada implementação de CLI MUST seguir.

#### Scenario: Runner executa e retorna output
- **WHEN** o método `run` é chamado com um prompt e o diretório de trabalho
- **THEN** o runner executa o CLI de IA correspondente e retorna a saída como string

### Requirement: Runner para Gemini CLI
O sistema SHALL implementar `GeminiCLIRunner` que executa o prompt via `gemini` CLI, passando o prompt como argumento ou via arquivo temporário.

#### Scenario: Execução com sucesso
- **WHEN** o gemini CLI está instalado e configurado
- **THEN** o runner executa `gemini` com o prompt e retorna o output completo

#### Scenario: Gemini CLI não instalado
- **WHEN** o comando `gemini` não é encontrado no PATH
- **THEN** o runner lança erro com mensagem: "gemini-cli não encontrado. Instale em: https://github.com/google-gemini/gemini-cli"

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

### Requirement: Seleção de runner via parâmetro CLI
O sistema SHALL permitir selecionar o runner via flag `--runner` (ex: `--runner gemini`, `--runner copilot`), com `gemini` como valor default.

#### Scenario: Runner selecionado via flag
- **WHEN** o usuário executa `airev review --base main --runner copilot`
- **THEN** o sistema usa o `CopilotCLIRunner` para executar a análise

#### Scenario: Runner inválido
- **WHEN** o usuário passa `--runner xyz` e não existe implementação para `xyz`
- **THEN** o sistema exibe erro listando os runners disponíveis

### Requirement: Verificar disponibilidade do CLI no startup
O sistema SHALL verificar se o CLI de IA selecionado está instalado e acessível antes de iniciar a análise.

#### Scenario: CLI disponível
- **WHEN** o runner selecionado verifica que o CLI está no PATH
- **THEN** a análise prossegue normalmente

#### Scenario: CLI indisponível
- **WHEN** o CLI não está instalado
- **THEN** o sistema encerra com mensagem de erro antes de fazer qualquer processamento
