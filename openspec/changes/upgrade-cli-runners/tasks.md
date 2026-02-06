## 1. Copilot Runner - Migração para Standalone

- [x] 1.1 Remover método `_check_gh_extension_available()` do CopilotCLIRunner
- [x] 1.2 Remover método `_run_gh_extension()` do CopilotCLIRunner
- [x] 1.3 Remover atributo `_cli_mode` e lógica de detecção de modo
- [x] 1.4 Atualizar `_check_standalone_available()` para verificar comando `copilot`
- [x] 1.5 Reescrever método `run()` para usar `copilot --yolo --silent` com prompt via stdin
- [x] 1.6 Atualizar mensagem de erro com instruções de instalação do copilot standalone

## 2. Gemini Runner - Ajustes para Contexto Expandido

- [x] 2.1 Verificar se flag `-y` está sendo usado corretamente (já está)
- [x] 2.2 Garantir que `cwd=workdir` está sendo passado corretamente no subprocess

## 3. Spec e Documentação

- [x] 3.1 Atualizar docstring do CopilotCLIRunner com novas instruções de instalação
- [x] 3.2 Remover referências ao `gh copilot` da documentação do runner

## 4. Testes

- [x] 4.1 Atualizar/criar testes para CopilotCLIRunner com nova implementação
- [x] 4.2 Verificar testes existentes do GeminiCLIRunner
