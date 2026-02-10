## Why

O prompt atual de code review é genérico e gera falsos positivos. Ferramentas de mercado como PR-Agent, CodeRabbit e Gito investem em técnicas específicas para reduzir ruído: persona clara, regras anti-falsos positivos, score de confiança e categorias mais granulares. Além disso, falta detecção de breaking changes em APIs, um problema comum em PRs.

## What Changes

### Fase 1: Reduzir Ruído
- Persona clara no prompt ("revisor de código sênior")
- Seção detalhada de regras anti-falsos positivos (6+ regras)
- Campo `confidence` (1-10) em cada finding no modelo e parser
- Filtragem por confidence via CLI com flag `--min-confidence` (default: 7)
- Nova categoria `error-handling` para tratamento de erros
- Nova categoria `breaking-change` para quebra de contratos em APIs REST
- Definições claras de severidade (CRITICAL/WARNING/INFO)
- Instruções específicas para detectar breaking changes em Pydantic models e OpenAPI

### Fase 2: Refinamentos
- Few-shot examples no prompt (1-2 exemplos de findings bem formatados)
- Triagem LGTM/NEEDS_REVIEW (classificar arquivo antes de revisar para economizar tokens)
- Boas práticas encontradas (reforço positivo - elogiar código bem feito)

## Capabilities

### New Capabilities

- `breaking-change-detection`: Detecção de quebra de contratos em APIs REST
- `confidence-filtering`: Filtragem de findings por score de confiança no CLI
- `few-shot-examples`: Exemplos de findings no prompt para guiar a LLM
- `file-triage`: Triagem LGTM/NEEDS_REVIEW antes do review detalhado
- `good-practices`: Identificação de boas práticas no código

### Modified Capabilities

- `prompt-building`: Adicionar persona, regras anti-ruído, categorias, severidade, few-shot, triagem, boas práticas
- `response-parsing`: Parsear campo confidence e good_practices

## Impact

- `src/code_reviewer/prompts/review_system.md`: Reescrita completa do template
- `src/code_reviewer/models.py`: Novo campo `confidence` em Finding, novas categorias, modelo para boas práticas
- `src/code_reviewer/response_parser.py`: Parsear confidence e good_practices
- `src/code_reviewer/cli.py`: Nova flag `--min-confidence` com default 7
