## ADDED Requirements

### Requirement: Incluir descrição das alterações no prompt
O sistema SHALL incluir uma seção de descrição das alterações no prompt quando fornecida pelo usuário.

#### Scenario: Descrição presente no prompt
- **WHEN** o usuário forneceu descrição (via flag ou interativamente)
- **THEN** o prompt contém uma seção "DESCRIÇÃO DAS ALTERAÇÕES" com o texto fornecido

#### Scenario: Descrição ausente não aparece no prompt
- **WHEN** o usuário não forneceu descrição
- **THEN** o prompt não contém a seção "DESCRIÇÃO DAS ALTERAÇÕES"

#### Scenario: Posicionamento da seção de descrição
- **WHEN** a descrição é incluída no prompt
- **THEN** a seção aparece após "REGRAS IMPORTANTES" e antes de "FOCO DA ANÁLISE"

### Requirement: Suportar placeholder de descrição no template
O sistema SHALL suportar um placeholder `{description}` no template do prompt que é substituído pela seção de descrição ou string vazia.

#### Scenario: Placeholder substituído com descrição
- **WHEN** descrição foi fornecida
- **THEN** o placeholder `{description}` é substituído pela seção formatada

#### Scenario: Placeholder substituído sem descrição
- **WHEN** descrição não foi fornecida
- **THEN** o placeholder `{description}` é substituído por string vazia
