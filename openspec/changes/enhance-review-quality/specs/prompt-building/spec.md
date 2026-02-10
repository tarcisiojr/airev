## ADDED Requirements

### Requirement: Incluir persona clara no prompt
O sistema SHALL definir a persona "revisor de código sênior" no início do prompt, estabelecendo expertise e propósito.

#### Scenario: Persona presente no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt inicia com texto similar a: "Você é um revisor de código sênior especializado em segurança, performance e qualidade de software. Sua função é fornecer feedback construtivo, acionável e de alta confiança."

### Requirement: Incluir princípios fundamentais no prompt
O sistema SHALL incluir uma seção de princípios fundamentais com 5 itens: foco nas mudanças, contexto como referência, alta confiança, acionável, sem ruído.

#### Scenario: Princípios presentes no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção "PRINCÍPIOS FUNDAMENTAIS" com os 5 itens listados

### Requirement: Incluir regras anti-falsos positivos no prompt
O sistema SHALL incluir uma seção de regras anti-falsos positivos com pelo menos 6 regras específicas para evitar findings irrelevantes.

#### Scenario: Regras anti-ruído presentes
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção "REGRAS ANTI-FALSOS POSITIVOS" incluindo: não questionar imports, não tratar escopo aberto como incompleto, não sugerir em código não alterado, não reportar sintaxe baseado em diff parcial, não duplicar funcionalidade, não sugerir refatorações sem benefício claro

### Requirement: Incluir categoria error-handling no prompt
O sistema SHALL incluir a categoria "Tratamento de Erros" nas instruções de análise.

#### Scenario: Categoria error-handling presente
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção de "Tratamento de Erros (WARNING)" listando: exceções silenciadas, catch genérico, falta de logging, promises sem catch

### Requirement: Incluir categoria breaking-change no prompt
O sistema SHALL incluir a categoria "Breaking Changes em APIs" nas instruções de análise.

#### Scenario: Categoria breaking-change presente
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção "Breaking Changes em APIs (WARNING)" listando os patterns a detectar: remoção de campos, campos opcionais tornados obrigatórios, mudança de tipo, remoção de endpoints, valores de enum removidos

### Requirement: Incluir definições de severidade no prompt
O sistema SHALL incluir definições claras do que cada nível de severidade significa.

#### Scenario: Definições de severidade presentes
- **WHEN** o prompt é montado
- **THEN** o prompt contém seção "SEVERIDADE" definindo: CRITICAL (vulnerabilidade, crash, perda de dados), WARNING (bug potencial, performance, breaking change), INFO (robustez, boa prática)

### Requirement: Incluir campo confidence no schema JSON do prompt
O sistema SHALL incluir o campo `confidence` (1-10) no schema JSON de exemplo do prompt.

#### Scenario: Schema com confidence
- **WHEN** o prompt é montado
- **THEN** o JSON_SCHEMA_EXAMPLE contém campo "confidence" com valor de exemplo (ex: 8)

### Requirement: Instruir LLM sobre priorização por confidence
O sistema SHALL instruir a LLM a priorizar findings de alta confiança e sempre incluir o score.

#### Scenario: Instrução de confidence presente
- **WHEN** o prompt é montado
- **THEN** o prompt contém instrução similar a: "Priorize findings com confiança ≥7. Sempre inclua o score de confiança (1-10) em cada finding."
