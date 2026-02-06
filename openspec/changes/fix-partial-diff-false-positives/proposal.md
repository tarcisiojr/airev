## Why

A LLM está gerando falsos positivos de erros de sintaxe ao analisar apenas o trecho do diff. Quando o diff mostra código parcial (ex: abertura de bloco sem fechamento), a LLM reporta erro de sintaxe mesmo quando o código completo no arquivo original está correto. Isso gera ruído na revisão e diminui a confiança do usuário nos resultados.

## What Changes

- Adicionar instruções explícitas no prompt para evitar falsos positivos de análise parcial
- Instruir a LLM a usar o contexto completo do arquivo (seção ARQUIVOS MODIFICADOS) para validar questões de sintaxe antes de reportar
- Adicionar regra clara: "Não reportar erros de sintaxe baseados apenas no diff parcial"
- Incluir exemplos de falsos positivos a evitar

## Capabilities

### New Capabilities

_Nenhuma nova capability necessária._

### Modified Capabilities

- `prompt-building`: Adicionar requisito para incluir instruções anti-falso-positivo no prompt, orientando a LLM a não reportar erros de sintaxe baseados apenas em código parcial do diff

## Impact

- **Arquivos afetados**: `src/code_reviewer/prompts/review_system.md`
- **Specs afetadas**: `openspec/specs/prompt-building/spec.md` (delta spec necessário)
- **Risco**: Baixo - mudança isolada no prompt de sistema
- **Benefício**: Redução de falsos positivos, maior precisão da revisão
