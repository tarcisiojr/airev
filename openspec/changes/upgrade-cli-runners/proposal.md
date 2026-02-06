## Why

As ferramentas CLI de IA (Gemini CLI, GitHub Copilot CLI) evoluíram e agora oferecem capacidades "agentic" - podem ler arquivos, buscar contexto adicional e executar análises mais profundas. O runner do Copilot ainda usa `gh copilot explain` que foi **deprecated em Outubro/2025**. Precisamos atualizar os runners para usar as versões modernas e habilitar análises mais ricas.

## What Changes

- **BREAKING**: Remover suporte a `gh copilot explain` (deprecated)
- Migrar Copilot runner para usar `copilot` CLI standalone com flags `--yolo --silent`
- Atualizar Gemini runner para instruir uso de contexto expandido no prompt
- Habilitar capacidades agentic (auto-approve de tools) para análises mais profundas
- Adicionar suporte a passar arquivos relacionados ao diff como contexto

## Capabilities

### New Capabilities

_Nenhuma nova capability - apenas modificações nas existentes._

### Modified Capabilities

- `ai-runner`: Atualizar requirements para refletir nova API do Copilot CLI standalone e capacidades agentic de ambos os runners

## Impact

- `src/code_reviewer/runners/copilot.py`: Reescrever para usar `copilot` standalone
- `src/code_reviewer/runners/gemini.py`: Ajustar flags e prompt para contexto expandido
- `openspec/specs/ai-runner/spec.md`: Atualizar requirements deprecados
- Documentação de instalação do Copilot precisa ser atualizada
