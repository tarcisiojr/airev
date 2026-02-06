## 1. Refatorar detecção de disponibilidade

- [x] 1.1 Adicionar método `_check_standalone_available()` para verificar comando `copilot`
- [x] 1.2 Adicionar método `_check_gh_extension_available()` para verificar `gh copilot`
- [x] 1.3 Adicionar atributo `_cli_mode` para armazenar modo detectado ("standalone" | "gh-extension" | None)
- [x] 1.4 Refatorar `check_availability()` para verificar standalone primeiro, depois gh-extension

## 2. Refatorar execução do comando

- [x] 2.1 Criar método `_run_standalone(prompt, workdir)` para executar via `copilot`
- [x] 2.2 Renomear lógica atual para `_run_gh_extension(prompt, workdir)`
- [x] 2.3 Atualizar `run()` para chamar o método correto baseado em `_cli_mode`

## 3. Atualizar mensagens de erro

- [x] 3.1 Atualizar mensagem de `RunnerNotFoundError` para listar ambas as opções de instalação

## 4. Testes

- [x] 4.1 Adicionar teste para cenário com `copilot` standalone disponível
- [x] 4.2 Adicionar teste para cenário com fallback para `gh copilot`
- [x] 4.3 Adicionar teste para cenário sem nenhum Copilot instalado
