## 1. Modelo e Enums

- [x] 1.1 Adicionar `BREAKING_CHANGE = "breaking-change"` ao enum Category em models.py
- [x] 1.2 Adicionar `ERROR_HANDLING = "error-handling"` ao enum Category em models.py
- [x] 1.3 Adicionar campo `confidence: int = Field(default=10, ge=1, le=10)` ao modelo Finding
- [x] 1.4 Criar modelo `GoodPractice` com campos file, line, description
- [x] 1.5 Adicionar campo `good_practices: list[GoodPractice]` ao ReviewResult

## 2. Response Parser

- [x] 2.1 Atualizar parsing para extrair campo confidence com fallback para 10
- [x] 2.2 Adicionar validação de range (1-10) no parsing de confidence
- [x] 2.3 Adicionar suporte às novas categorias (breaking-change, error-handling) no mapeamento
- [x] 2.4 Adicionar parsing de good_practices do response

## 3. Prompt Template

- [x] 3.1 Reescrever seção inicial com persona clara ("revisor de código sênior")
- [x] 3.2 Adicionar seção "PRINCÍPIOS FUNDAMENTAIS" com 5 itens
- [x] 3.3 Adicionar seção "REGRAS ANTI-FALSOS POSITIVOS" com 6+ regras
- [x] 3.4 Adicionar categoria "Tratamento de Erros (WARNING)" nas instruções
- [x] 3.5 Adicionar categoria "Breaking Changes em APIs (WARNING)" com patterns detalhados
- [x] 3.6 Adicionar seção "SEVERIDADE" com definições claras
- [x] 3.7 Adicionar instrução sobre priorização por confidence

## 4. Refinamentos

- [x] 4.1 Adicionar seção "EXEMPLOS" com 1-2 few-shot examples de findings
- [x] 4.2 Adicionar instrução de triagem LGTM/NEEDS_REVIEW por arquivo
- [x] 4.3 Adicionar seção "BOAS PRÁTICAS" instruindo a elogiar código bem feito
- [x] 4.4 Atualizar schema JSON com campo good_practices

## 5. CLI

- [x] 5.1 Adicionar opção `--min-confidence` com default 7 ao comando review
- [x] 5.2 Implementar filtragem de findings por confidence antes de exibir
- [x] 5.3 Recalcular summary após filtragem
