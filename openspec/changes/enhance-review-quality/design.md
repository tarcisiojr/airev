## Context

O prompt atual de code review é genérico e produz falsos positivos. A pesquisa de mercado (PR-Agent, CodeRabbit, Gito, GitHub Copilot) identificou técnicas específicas para melhorar a qualidade: persona clara, regras anti-ruído, score de confiança, detecção de breaking changes, few-shot examples e reforço positivo.

O sistema atual usa:
- Template em `prompts/review_system.md` com placeholders
- Modelo `Finding` com campos básicos (file, line, severity, category, title, description, suggestion, code_snippet)
- Enum `Category` com 5 valores (security, performance, bug, resource-leak, text-quality)

## Goals / Non-Goals

**Goals:**
- Reduzir falsos positivos com regras anti-ruído no prompt
- Adicionar score de confiança no modelo e parser
- Filtrar findings por confidence via CLI (default: 7)
- Detectar breaking changes em APIs REST (Pydantic models, OpenAPI)
- Melhorar a estrutura do prompt com persona e categorias claras
- Incluir few-shot examples para guiar a LLM
- Implementar triagem LGTM/NEEDS_REVIEW para economizar tokens
- Identificar boas práticas para reforço positivo

**Non-Goals:**
- Separação de prompts (inline vs summary) - complexidade desnecessária

## Decisions

### D1: Campo confidence como inteiro 1-10

**Decisão**: Adicionar `confidence: int` com constraint `ge=1, le=10` no modelo Finding.

**Rationale**: Escala 1-10 é intuitiva e alinha com PR-Agent/Gito. Inteiro é mais simples que float.

### D2: Default de confidence para findings sem o campo

**Decisão**: Se a LLM não retornar confidence, usar `10` como fallback (assumir alta confiança).

**Rationale**: Mantém compatibilidade com respostas antigas, não penaliza findings legítimos.

### D3: Filtragem de confidence client-side com default 7

**Decisão**: Filtrar findings no CLI com flag `--min-confidence N` (default: 7).

**Alternativas consideradas**:
- LLM-side (só retornar confidence ≥7): Menos tokens, mas perde dados para tuning
- Sem filtragem: Muito ruído para o usuário

**Rationale**: Permite ajustar threshold sem re-rodar, habilita modo verbose com `--min-confidence 1`.

### D4: Categoria breaking-change como WARNING por default

**Decisão**: Breaking changes têm severidade WARNING, não CRITICAL.

**Alternativas consideradas**:
- CRITICAL: Muito alarmista para APIs internas
- Configurável: Complexidade desnecessária

**Rationale**: Breaking changes são importantes mas nem sempre críticos. O dev pode avaliar o impacto.

### D5: Estrutura do prompt com seções bem definidas

**Decisão**: Reestruturar o prompt com seções:
1. Persona e propósito
2. Princípios fundamentais (5 itens)
3. Regras anti-falsos positivos (6+ regras)
4. Categorias de análise (incluindo breaking-change e error-handling)
5. Definições de severidade
6. Few-shot examples (1-2 exemplos)
7. Schema JSON com confidence e good_practices
8. Diff, contexto e referências

**Rationale**: Estrutura clara ajuda a LLM a seguir instruções. Alinha com padrões de mercado.

### D6: Few-shot examples inline no prompt

**Decisão**: Incluir 1-2 exemplos de findings bem formatados diretamente no prompt.

**Alternativas consideradas**:
- Arquivo separado: Mais difícil de manter sincronizado
- Nenhum exemplo: Menos consistência na saída

**Rationale**: Few-shot melhora consistência da saída. 1-2 exemplos são suficientes sem aumentar muito o prompt.

### D7: Triagem LGTM/NEEDS_REVIEW no início

**Decisão**: Instruir a LLM a classificar cada arquivo como LGTM ou NEEDS_REVIEW antes de detalhar findings.

**Rationale**: Economiza tokens em arquivos sem problemas. Inspirado no CodeRabbit.

### D8: Seção de boas práticas no output

**Decisão**: Adicionar campo opcional `good_practices` no schema para a LLM elogiar código bem feito.

**Rationale**: Reforço positivo motiva o desenvolvedor. Inspirado no GitHub Copilot.

## Risks / Trade-offs

### R1: Prompt maior = mais tokens de entrada
**Risco**: Custo maior por request com few-shot e seções extras.
**Mitigação**: O ganho em qualidade compensa. Prompt ainda < 3K tokens.

### R2: Confidence pode ser inconsistente entre modelos
**Risco**: Diferentes LLMs podem calibrar confidence de formas diferentes.
**Mitigação**: Default alto (10), threshold ajustável via `--min-confidence`.

### R3: Breaking change detection é heurístico
**Risco**: Pode não detectar todos os casos ou gerar falsos positivos.
**Mitigação**: Instruções detalhadas no prompt, severidade WARNING, feedback loop com usuários.

### R4: Triagem pode perder findings
**Risco**: Arquivo marcado como LGTM pode ter problemas sutis.
**Mitigação**: Instruir LLM a ser conservadora - na dúvida, NEEDS_REVIEW.
