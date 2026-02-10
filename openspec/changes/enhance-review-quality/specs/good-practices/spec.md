## ADDED Requirements

### Requirement: Modelo GoodPractice
O sistema SHALL incluir um modelo `GoodPractice` com campos file, line e description para representar boas práticas encontradas.

#### Scenario: Modelo GoodPractice definido
- **WHEN** o módulo models.py é carregado
- **THEN** existe uma classe GoodPractice com campos file (str), line (int) e description (str)

### Requirement: Campo good_practices no ReviewResult
O sistema SHALL incluir um campo opcional `good_practices` no modelo ReviewResult.

#### Scenario: ReviewResult com good_practices
- **WHEN** um ReviewResult é criado
- **THEN** o campo good_practices aceita uma lista de GoodPractice

### Requirement: Instruir LLM a identificar boas práticas
O sistema SHALL instruir a LLM a identificar e elogiar boas práticas no código revisado.

#### Scenario: Instrução de boas práticas presente no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção "BOAS PRÁTICAS" instruindo a LLM a elogiar código bem feito

#### Scenario: Exemplo de boa prática
- **WHEN** a LLM identifica uso de pattern adequado, tratamento de erro exemplar, ou código bem documentado
- **THEN** a LLM inclui uma GoodPractice no response

### Requirement: Parsing de good_practices
O sistema SHALL parsear o campo good_practices do response da LLM.

#### Scenario: Good practices presente e válido
- **WHEN** a LLM retorna um response com good_practices
- **THEN** o parser extrai a lista de GoodPractice

#### Scenario: Good practices ausente
- **WHEN** a LLM retorna um response sem good_practices
- **THEN** o parser usa lista vazia como default
