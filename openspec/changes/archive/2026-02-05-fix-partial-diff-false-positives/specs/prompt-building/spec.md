## ADDED Requirements

### Requirement: Incluir aviso anti-falso-positivo para análise de diff parcial
O sistema SHALL incluir no prompt uma instrução explícita alertando a LLM que o diff mostra apenas código parcial e que ela MUST consultar a seção "ARQUIVOS MODIFICADOS" antes de reportar erros de sintaxe ou código incompleto.

#### Scenario: Aviso presente no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt contém instrução similar a: "IMPORTANTE: O diff mostra apenas as linhas alteradas. Código aparentemente incompleto (blocos abertos, imports parciais) pode estar completo no arquivo original. SEMPRE consulte a seção 'ARQUIVOS MODIFICADOS' antes de reportar erros de sintaxe ou código incompleto."

#### Scenario: Posicionamento do aviso
- **WHEN** o prompt é montado
- **THEN** o aviso é posicionado após a seção "REGRAS IMPORTANTES" e antes da seção "FOCO DA ANÁLISE"

#### Scenario: LLM não reporta falso positivo de sintaxe
- **WHEN** o diff mostra código parcial (ex: abertura de bloco sem fechamento visível)
- **AND** o arquivo completo na seção "ARQUIVOS MODIFICADOS" mostra código sintaticamente correto
- **THEN** a LLM não reporta erro de sintaxe para esse trecho
