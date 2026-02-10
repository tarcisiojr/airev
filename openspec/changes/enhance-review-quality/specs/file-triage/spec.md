## ADDED Requirements

### Requirement: Instruir triagem LGTM/NEEDS_REVIEW por arquivo
O sistema SHALL instruir a LLM a classificar cada arquivo como LGTM ou NEEDS_REVIEW antes de detalhar findings.

#### Scenario: Instrução de triagem presente no prompt
- **WHEN** o prompt é montado
- **THEN** o prompt contém instrução para classificar arquivos antes de revisar em detalhe

#### Scenario: Arquivo LGTM não gera findings
- **WHEN** a LLM classifica um arquivo como LGTM
- **THEN** nenhum finding é gerado para esse arquivo

#### Scenario: Arquivo NEEDS_REVIEW recebe análise detalhada
- **WHEN** a LLM classifica um arquivo como NEEDS_REVIEW
- **THEN** a LLM analisa o arquivo e gera findings se encontrar problemas

### Requirement: Triagem conservadora
O sistema SHALL instruir a LLM a ser conservadora na triagem - na dúvida, classificar como NEEDS_REVIEW.

#### Scenario: Instrução de conservadorismo presente
- **WHEN** o prompt é montado
- **THEN** o prompt contém instrução similar a: "Na dúvida, classifique como NEEDS_REVIEW"
