## ADDED Requirements

### Requirement: Campo confidence no modelo Finding
O sistema SHALL incluir um campo `confidence` (inteiro 1-10) em cada Finding retornado pela LLM.

#### Scenario: Finding com confidence presente
- **WHEN** a LLM retorna um finding com `"confidence": 8`
- **THEN** o modelo Finding armazena o valor 8 no campo confidence

#### Scenario: Finding sem confidence (fallback)
- **WHEN** a LLM retorna um finding sem o campo confidence
- **THEN** o modelo Finding usa o valor default 10

#### Scenario: Confidence fora do range (alto)
- **WHEN** a LLM retorna um finding com `"confidence": 15`
- **THEN** o Finding parseado tem confidence=10

#### Scenario: Confidence fora do range (baixo)
- **WHEN** a LLM retorna um finding com `"confidence": 0`
- **THEN** o Finding parseado tem confidence=1

### Requirement: Flag --min-confidence no CLI
O sistema SHALL aceitar uma flag `--min-confidence N` no comando `review` para filtrar findings.

#### Scenario: Filtragem com threshold default
- **WHEN** o usuário executa `airev review --base main` sem especificar --min-confidence
- **THEN** apenas findings com confidence >= 7 são exibidos

#### Scenario: Filtragem com threshold customizado
- **WHEN** o usuário executa `airev review --base main --min-confidence 5`
- **THEN** apenas findings com confidence >= 5 são exibidos

#### Scenario: Ver todos os findings
- **WHEN** o usuário executa `airev review --base main --min-confidence 1`
- **THEN** todos os findings são exibidos, independente do confidence

### Requirement: Summary reflete filtragem
O sistema SHALL atualizar o summary para refletir apenas os findings após filtragem por confidence.

#### Scenario: Summary com findings filtrados
- **WHEN** a LLM retorna 5 findings mas apenas 3 têm confidence >= threshold
- **THEN** o summary mostra total=3 e as contagens por severidade consideram apenas os 3 findings
