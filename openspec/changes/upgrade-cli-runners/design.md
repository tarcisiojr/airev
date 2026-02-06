## Context

Os runners atuais tratam as CLIs de IA como "caixas pretas passivas" - enviamos um prompt e recebemos uma resposta. No entanto, tanto Gemini CLI quanto GitHub Copilot CLI evoluíram para agentes com capacidades de:
- Ler arquivos locais
- Buscar contexto adicional automaticamente
- Usar ferramentas (tools) para análises mais profundas

O runner do Copilot ainda usa `gh copilot explain` que foi deprecated em Outubro/2025, substituído pelo `copilot` CLI standalone.

## Goals / Non-Goals

**Goals:**
- Migrar Copilot runner para `copilot` CLI standalone
- Habilitar modo "agentic" com auto-approve de tools
- Manter compatibilidade com CI/CD (output limpo, sem interatividade)
- Permitir análises mais profundas via contexto expandido

**Non-Goals:**
- Não vamos implementar novos runners (apenas atualizar os existentes)
- Não vamos mudar a interface `AIRunner` - o contrato `run(prompt, workdir)` permanece
- Não vamos implementar streaming de output (manter comportamento síncrono)

## Decisions

### D1: Copilot - Usar `copilot` standalone com `--yolo --silent`

**Escolha**: Migrar de `gh copilot explain` para `copilot --yolo --silent`

**Alternativas consideradas**:
1. Manter `gh copilot` com fallback → Deprecated, será removido
2. Suportar ambos (gh e standalone) → Complexidade desnecessária
3. Usar apenas `copilot` standalone → **Escolhido** - é o caminho oficial

**Rationale**: O `gh copilot` foi oficialmente deprecated. O novo `copilot` CLI oferece `--yolo` (auto-approve all tools) e `--silent` (output limpo para CI).

### D2: Gemini - Manter `-y` e confiar no contexto automático

**Escolha**: Continuar usando `gemini -y` (YOLO mode) que já auto-aprova tools

**Rationale**: O Gemini CLI com `-y` já pode ler arquivos e buscar contexto. Não precisamos de flags adicionais - apenas garantir que o prompt instrua a ferramenta a explorar o contexto quando necessário.

### D3: Passar workdir corretamente para ambos runners

**Escolha**: Garantir que o `cwd` do subprocess seja o diretório do projeto

**Rationale**: Ambas as ferramentas usam o diretório atual como raiz para buscar contexto. Passando o workdir correto, habilitamos a capacidade de ler arquivos relacionados.

### D4: Remover código legado do Copilot runner

**Escolha**: Remover completamente os métodos `_check_gh_extension_available`, `_run_gh_extension` e lógica de detecção de modo

**Rationale**: Simplifica o código, remove dependência do `gh` CLI, e segue a direção oficial do GitHub.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Usuários sem `copilot` instalado terão erro | Mensagem de erro clara com instruções de instalação atualizadas |
| `--yolo` pode executar ações indesejadas | O contexto é controlado (apenas análise de diff, não modificações) |
| Mudança breaking para quem usa `gh copilot` | Documentar migração na mensagem de erro |
| Análises podem demorar mais com contexto expandido | Aceitável - trade-off por qualidade |
