## ADDED Requirements

### Requirement: Montar prompt com seções estruturadas
O sistema SHALL montar um prompt contendo seções claramente delimitadas: REGRAS, DIFF, ARQUIVOS MODIFICADOS e REFERÊNCIAS (backtracking).

#### Scenario: Prompt completo com todas as seções
- **WHEN** o diff e o contexto foram extraídos com sucesso
- **THEN** o prompt contém as 4 seções separadas por delimitadores claros, com o diff completo, conteúdo dos arquivos e referências de backtracking

### Requirement: Incluir regras de escopo no prompt
O sistema SHALL incluir instruções explícitas para que a IA analise APENAS as linhas adicionadas/modificadas no diff, usando o contexto e referências apenas para entender a mudança, sem sugerir melhorias em código não alterado.

#### Scenario: Regras de escopo presentes
- **WHEN** o prompt é montado
- **THEN** o prompt contém instrução explícita: "Analise APENAS as mudanças marcadas com + no DIFF. Use CONTEXTO e REFERÊNCIAS para entender a mudança, NÃO para sugerir melhorias em código existente."

### Requirement: Incluir schema JSON esperado no prompt
O sistema SHALL incluir no prompt o schema JSON exato que a IA MUST retornar, com exemplo de um finding completo.

#### Scenario: Schema presente no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt contém o schema JSON com campos: file, line, severity, category, title, description, suggestion, code_snippet

### Requirement: Incluir categorias de análise no prompt
O sistema SHALL instruir a IA a focar nas categorias: segurança (injection, XSS, secrets), performance (N+1, loops), bugs potenciais (null, race condition) e recursos não fechados (connections, files).

#### Scenario: Categorias listadas
- **WHEN** o prompt é montado
- **THEN** o prompt contém lista explícita das categorias de análise com exemplos

### Requirement: Carregar template de prompt de arquivo externo
O sistema SHALL carregar o system prompt de um arquivo markdown (`prompts/review_system.md`) e substituir placeholders (`{diff}`, `{context}`, `{references}`, `{json_schema}`) pelos valores reais.

#### Scenario: Template carregado e preenchido
- **WHEN** o prompt builder é chamado com diff, contexto e referências
- **THEN** o arquivo template é lido, placeholders são substituídos e o prompt final é retornado como string

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
