## Context

O sistema de atualização do airev usa um cache local (`~/.cache/airev/update-check.json`) com TTL de 1 hora para evitar requests excessivos ao PyPI. O comando `airev upgrade` verifica este cache, executa `pipx upgrade airev` (ou pip), e reporta sucesso baseado apenas no exit code do comando.

**Problema atual:** O cache não é invalidado após upgrade, e o resultado do upgrade não é verificado. Isso causa:
1. `airev upgrade` reporta "Atualizado para X" mesmo quando nada mudou
2. Comandos subsequentes continuam mostrando "atualização disponível"

## Goals / Non-Goals

**Goals:**
- Invalidar cache após executar upgrade (independente do resultado)
- Verificar se a versão realmente mudou após upgrade
- Fornecer feedback preciso ao usuário sobre o resultado

**Non-Goals:**
- Mudar a lógica de verificação de versão no PyPI
- Alterar o TTL do cache
- Suportar outros instaladores além de pipx/pip

## Decisions

### 1. Adicionar função para limpar o cache

**Decisão:** Criar `clear_cache()` em `version_check.py` e chamá-la após qualquer tentativa de upgrade.

**Alternativas consideradas:**
- Reduzir TTL do cache → Não resolve o problema imediato, aumenta requests ao PyPI
- Invalidar apenas em sucesso → Pode deixar cache inconsistente em falhas

**Rationale:** Limpar sempre garante que a próxima verificação reflita o estado real.

### 2. Verificar versão após upgrade

**Decisão:** Após executar o comando de upgrade, reimportar `__version__` não funciona (módulo já carregado). Em vez disso, verificar via `pipx list --json` ou `pip show airev`.

**Alternativas consideradas:**
- Confiar apenas no exit code → Atual, não confiável (pipx retorna 0 mesmo sem mudança)
- Reiniciar o processo → Complexo e má experiência de usuário

**Rationale:** Consultar o instalador diretamente dá a versão real instalada.

### 3. Mensagens de feedback

**Decisão:** Três cenários de mensagem:
1. "Já está na versão mais recente" → Quando PyPI e local são iguais
2. "Atualizado de X para Y" → Quando versão realmente mudou
3. "Atualização disponível, mas falhou" → Quando upgrade não teve efeito

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| `pipx list --json` pode não estar disponível em versões antigas | Fallback para confiar no exit code com aviso |
| Performance adicional ao verificar versão | Operação rara (apenas em upgrade), impacto negligenciável |
| Cache pode ser limpo mas PyPI estar indisponível | Próxima verificação simplesmente falhará silenciosamente (comportamento atual) |
