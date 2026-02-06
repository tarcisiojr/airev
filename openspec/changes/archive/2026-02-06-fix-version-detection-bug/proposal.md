## Why

O comando `airev upgrade` reporta sucesso na atualização mesmo quando nenhuma atualização real ocorre, e não invalida o cache de versão após executar. Isso causa confusão: o usuário vê "Atualizado para versão X" mas ao rodar qualquer comando, continua vendo o aviso de "Nova versão disponível".

## What Changes

- Invalidar o cache de verificação de versão após executar upgrade (sucesso ou falha)
- Verificar se a atualização realmente ocorreu comparando versões antes/depois
- Reportar corretamente quando o pacote já está atualizado via pipx/pip

## Capabilities

### New Capabilities

_Nenhuma nova capacidade - este é um fix de comportamento existente._

### Modified Capabilities

- `updater`: Corrigir lógica de upgrade para invalidar cache e verificar resultado real da atualização

## Impact

- **Código afetado**: `src/code_reviewer/updater/upgrade.py`, `src/code_reviewer/updater/version_check.py`
- **Comportamento**: Após upgrade, o cache será limpo e a próxima verificação consultará o PyPI novamente
- **UX**: Mensagens mais precisas sobre o estado real da atualização
