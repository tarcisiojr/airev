## Context

O `CopilotCLIRunner` atual assume que todos os usuários utilizam `gh copilot` (extensão do GitHub CLI). Porém, existe também o comando `copilot` standalone (GitHub Copilot CLI), que é uma instalação separada.

**Estado atual:**
- `check_availability()` verifica se `gh` existe e se a extensão `copilot` está na lista de extensões
- `run()` executa `gh copilot explain <prompt>`

**Problema:**
Usuários com `copilot` CLI standalone recebem "Runner não disponível" porque:
1. Podem não ter `gh` instalado
2. Mesmo tendo `gh`, a extensão pode não estar instalada

## Goals / Non-Goals

**Goals:**
- Detectar e suportar ambas as formas de instalação do Copilot CLI
- Manter compatibilidade com usuários que usam `gh copilot`
- Priorizar `copilot` standalone quando disponível (mais direto)

**Non-Goals:**
- Adicionar novos runners de IA
- Modificar a interface `AIRunner`
- Alterar comportamento de outros runners

## Decisions

### 1. Ordem de detecção: `copilot` primeiro, depois `gh copilot`

**Decisão:** Verificar `copilot` standalone primeiro, depois `gh copilot` como fallback.

**Alternativas consideradas:**
- Verificar `gh copilot` primeiro: descartado porque adiciona latência (precisa listar extensões)
- Perguntar ao usuário qual usar: descartado porque adiciona complexidade desnecessária

**Rationale:** O comando `copilot` standalone é mais direto e sua verificação é mais rápida (`which copilot` vs `gh extension list`).

### 2. Armazenar modo detectado para uso no `run()`

**Decisão:** Usar um atributo de instância `_cli_mode` para armazenar qual CLI foi detectado ("standalone" ou "gh-extension").

**Rationale:** Evita re-detectar a cada chamada de `run()`.

### 3. Comando standalone usa `copilot` diretamente

**Decisão:** Para o modo standalone, executar `copilot` passando o prompt como argumento ou via stdin.

**Nota:** Será necessário verificar a sintaxe exata do comando `copilot` standalone para garantir compatibilidade.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Sintaxe do `copilot` standalone pode diferir | Testar com instalação real antes de finalizar |
| Usuário pode ter ambos instalados com configs diferentes | Documentar ordem de prioridade; permitir override via env var no futuro se necessário |
| Cache de `_cli_mode` pode ficar stale se usuário instalar/desinstalar durante sessão | Aceitável - sessões são curtas |
