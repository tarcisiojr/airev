## Context

O airev atualmente analisa diffs de código usando IA, mas a IA não tem acesso à intenção do desenvolvedor. Em ambientes de CI, a descrição do PR/MR já existe e pode enriquecer o review. Em uso local, o desenvolvedor pode querer adicionar contexto antes da análise.

O projeto já usa `click` para CLI, `rich` para output, e tem lógica de detecção de TTY no `ProgressReporter`.

## Goals / Non-Goals

**Goals:**
- Permitir que o usuário forneça descrição via flag `--description`/`-d`
- Suportar leitura de descrição via stdin (`-d -`)
- Perguntar interativamente se não fornecida (em modo TTY)
- Suportar input multi-linha para permitir colar Markdown de PRs
- Integrar a descrição no prompt da IA

**Non-Goals:**
- Integração direta com APIs de GitHub/GitLab para buscar descrição automaticamente
- Validação ou formatação da descrição fornecida

## Decisions

### Decisão 1: Usar `prompt_toolkit` para input multi-linha

**Escolha**: Adicionar `prompt_toolkit` como dependência

**Alternativas consideradas**:
- `input()` padrão: Não suporta multi-linha nem bracketed paste
- `rich.Prompt`: Não suporta bracketed paste para multi-linha
- `click.prompt()`: Não suporta multi-linha

**Rationale**: `prompt_toolkit` suporta bracketed paste mode nativamente, permitindo colar texto com quebras de linha sem tratamento especial. É a mesma biblioteca usada por IPython, ptpython e outras CLIs profissionais.

### Decisão 2: Perguntar após mostrar o diff

**Escolha**: O prompt interativo aparece DEPOIS de exibir os arquivos modificados

**Rationale**: Ver quais arquivos foram alterados ajuda o usuário a lembrar/formular a descrição. Segue o fluxo mental natural de "o que mudei? ah sim, foi isso...".

### Decisão 3: Flag `--no-interactive` para CI

**Escolha**: Adicionar flag explícita ao invés de apenas detectar TTY

**Rationale**: Permite controle explícito. Um CI pode ter TTY em alguns casos, e o usuário pode querer forçar modo não-interativo mesmo localmente.

### Decisão 4: Suporte a stdin com `-d -`

**Escolha**: Usar a convenção Unix `-` para indicar leitura de stdin

**Alternativas consideradas**:
- Detectar automaticamente stdin: Pode conflitar com outros usos de pipe
- Flag separada `--description-file`: Redundante, stdin já resolve

**Rationale**: Padrão Unix bem conhecido. Permite `cat arquivo | airev -d -` e `airev -d - < arquivo`. Não bloqueia se stdin estiver vazio.

### Decisão 5: Seção opcional no prompt

**Escolha**: A seção `{description}` só aparece no prompt se descrição foi fornecida

**Rationale**: Não poluir o prompt com seções vazias. Se não há descrição, não incluir a seção.

## Risks / Trade-offs

- **[Nova dependência]** → `prompt_toolkit` é bem mantido e leve. Já é dependência transitiva do IPython, comum em ambientes de dev.
- **[UX do Ctrl+D]** → Alguns usuários podem não conhecer Ctrl+D para finalizar. Mitigação: instrução clara no prompt.
- **[Descrição muito longa]** → Pode aumentar tokens consumidos. Mitigação: Limitar a ~2000 caracteres com aviso.
