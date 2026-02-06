## Why

O runner `copilot` falha na verificação de disponibilidade porque assume que o usuário utiliza `gh copilot` (extensão do GitHub CLI), mas existe também o comando `copilot` standalone (GitHub Copilot CLI). Usuários com a instalação standalone recebem a mensagem "Runner 'copilot' não está disponível" mesmo tendo o Copilot funcional.

## What Changes

- Modificar `check_availability()` para detectar ambas as formas de instalação:
  1. `gh copilot` (extensão do GitHub CLI)
  2. `copilot` (CLI standalone)
- Ajustar o método `run()` para usar o comando correto baseado na instalação detectada
- Atualizar mensagens de erro para refletir ambas as opções de instalação

## Capabilities

### New Capabilities

_Nenhuma nova capability - é uma correção de bug._

### Modified Capabilities

_Nenhuma modificação de spec necessária - a interface do runner permanece a mesma._

## Impact

- **Código afetado**: `src/code_reviewer/runners/copilot.py`
  - `check_availability()` - lógica de detecção
  - `run()` - execução do comando
- **Comportamento**: Usuários com `copilot` CLI standalone poderão usar o runner
- **Compatibilidade**: Mantém suporte a `gh copilot` existente
