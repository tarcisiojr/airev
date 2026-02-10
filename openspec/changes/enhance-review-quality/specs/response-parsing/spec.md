## ADDED Requirements

### Requirement: Parsear campo confidence do Finding
O sistema SHALL parsear o campo `confidence` de cada finding retornado pela LLM.

#### Scenario: Confidence presente e válido
- **WHEN** a LLM retorna um finding com `"confidence": 8`
- **THEN** o Finding parseado tem confidence=8

#### Scenario: Confidence ausente
- **WHEN** a LLM retorna um finding sem o campo confidence
- **THEN** o Finding parseado tem confidence=10 (fallback)

#### Scenario: Confidence fora do range (alto)
- **WHEN** a LLM retorna um finding com `"confidence": 15`
- **THEN** o Finding parseado tem confidence=10

#### Scenario: Confidence fora do range (baixo)
- **WHEN** a LLM retorna um finding com `"confidence": 0`
- **THEN** o Finding parseado tem confidence=1

### Requirement: Parsear categoria breaking-change
O sistema SHALL aceitar a categoria "breaking-change" nos findings.

#### Scenario: Categoria breaking-change válida
- **WHEN** a LLM retorna um finding com `"category": "breaking-change"`
- **THEN** o Finding parseado tem category=Category.BREAKING_CHANGE

### Requirement: Parsear categoria error-handling
O sistema SHALL aceitar a categoria "error-handling" nos findings.

#### Scenario: Categoria error-handling válida
- **WHEN** a LLM retorna um finding com `"category": "error-handling"`
- **THEN** o Finding parseado tem category=Category.ERROR_HANDLING
