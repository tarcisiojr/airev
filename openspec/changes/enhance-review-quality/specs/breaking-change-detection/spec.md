## ADDED Requirements

### Requirement: Categoria breaking-change
O sistema SHALL incluir a categoria `breaking-change` no enum Category e instruir a LLM a detectar quebras de contrato em APIs.

#### Scenario: Finding de breaking change
- **WHEN** a LLM detecta remoção de campo em um Pydantic model de response
- **THEN** o finding tem category="breaking-change" e severity="WARNING"

### Requirement: Detectar remoção de campos em responses
O sistema SHALL instruir a LLM a identificar quando campos são removidos de modelos de response (Pydantic, TypedDict, dataclass).

#### Scenario: Campo removido de Pydantic model
- **WHEN** o diff mostra remoção de um campo de uma classe que herda de BaseModel
- **THEN** a LLM reporta um finding de breaking-change indicando o impacto em clientes

### Requirement: Detectar campos tornados obrigatórios
O sistema SHALL instruir a LLM a identificar quando campos opcionais tornam-se obrigatórios em requests.

#### Scenario: Campo opcional tornado obrigatório
- **WHEN** o diff mostra mudança de `field: Optional[str] = None` para `field: str`
- **THEN** a LLM reporta um finding de breaking-change indicando que clientes existentes podem falhar

### Requirement: Detectar mudança de tipo
O sistema SHALL instruir a LLM a identificar mudanças de tipo de dados em campos de API.

#### Scenario: Tipo alterado de string para int
- **WHEN** o diff mostra mudança de `user_id: str` para `user_id: int`
- **THEN** a LLM reporta um finding de breaking-change indicando incompatibilidade de tipo

### Requirement: Detectar remoção de endpoints
O sistema SHALL instruir a LLM a identificar remoção ou renomeação de rotas/endpoints.

#### Scenario: Endpoint removido
- **WHEN** o diff mostra remoção de um decorator `@app.get("/users/{id}")`
- **THEN** a LLM reporta um finding de breaking-change indicando endpoint indisponível

### Requirement: Detectar remoção de valores de enum
O sistema SHALL instruir a LLM a identificar quando valores são removidos de enums usados em APIs.

#### Scenario: Valor de enum removido
- **WHEN** o diff mostra remoção de um valor de um Enum (ex: `STATUS_PENDING = "pending"`)
- **THEN** a LLM reporta um finding de breaking-change indicando que clientes usando esse valor terão erros
