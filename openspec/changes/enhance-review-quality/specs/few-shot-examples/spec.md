## ADDED Requirements

### Requirement: Incluir few-shot examples no prompt
O sistema SHALL incluir 1-2 exemplos de findings bem formatados no prompt para guiar a LLM.

#### Scenario: Exemplos presentes no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção "EXEMPLOS" com pelo menos 1 finding de exemplo completo

#### Scenario: Exemplo cobre finding de segurança
- **WHEN** o prompt é montado
- **THEN** pelo menos um exemplo demonstra um finding de categoria security com todos os campos preenchidos

#### Scenario: Exemplo mostra confidence
- **WHEN** o prompt é montado
- **THEN** os exemplos incluem o campo confidence para demonstrar seu uso
