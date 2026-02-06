## ADDED Requirements

### Requirement: Version check on startup

O sistema DEVE verificar se há nova versão disponível no PyPI ao iniciar qualquer comando.

#### Scenario: Nova versão disponível
- **WHEN** usuário executa qualquer comando e existe versão mais recente no PyPI
- **THEN** sistema exibe notificação informando a versão disponível e comando para atualizar

#### Scenario: Versão atual é a mais recente
- **WHEN** usuário executa qualquer comando e está na versão mais recente
- **THEN** sistema não exibe nenhuma notificação de update

#### Scenario: Falha na verificação
- **WHEN** request ao PyPI falha (timeout, offline, erro)
- **THEN** sistema continua execução silenciosamente sem notificação

### Requirement: Cache de verificação

O sistema DEVE armazenar o resultado da verificação em cache local para evitar requests excessivos.

#### Scenario: Cache válido
- **WHEN** última verificação foi há menos de 1 hora
- **THEN** sistema usa versão do cache sem fazer novo request

#### Scenario: Cache expirado
- **WHEN** última verificação foi há mais de 1 hora
- **THEN** sistema faz novo request ao PyPI e atualiza o cache

#### Scenario: Cache inexistente ou corrompido
- **WHEN** arquivo de cache não existe ou está corrompido
- **THEN** sistema faz novo request ao PyPI e cria novo cache

### Requirement: Opt-out de verificação

O sistema DEVE permitir que usuário desabilite a verificação de updates.

#### Scenario: Variável de ambiente definida
- **WHEN** CODE_REVIEWER_NO_UPDATE_CHECK=1 está definida
- **THEN** sistema não faz verificação de versão

#### Scenario: Variável não definida
- **WHEN** CODE_REVIEWER_NO_UPDATE_CHECK não está definida ou é diferente de "1"
- **THEN** sistema faz verificação normalmente

### Requirement: Supressão em modo JSON

O sistema DEVE suprimir notificação de update quando output é JSON.

#### Scenario: Flag --json-output ativo
- **WHEN** usuário executa comando com --json-output
- **THEN** sistema não exibe notificação de update (para não poluir JSON)

### Requirement: Comando upgrade

O sistema DEVE fornecer comando `code-reviewer upgrade` para facilitar atualização.

#### Scenario: Update disponível via pipx
- **WHEN** usuário executa `code-reviewer upgrade` e foi instalado via pipx
- **THEN** sistema executa `pipx upgrade code-reviewer`

#### Scenario: Update disponível via pip
- **WHEN** usuário executa `code-reviewer upgrade` e foi instalado via pip
- **THEN** sistema executa `pip install --upgrade code-reviewer`

#### Scenario: Já está na versão mais recente
- **WHEN** usuário executa `code-reviewer upgrade` e já está na versão mais recente
- **THEN** sistema informa que já está atualizado

### Requirement: Timeout de verificação

O sistema DEVE respeitar timeout de 5 segundos para não bloquear execução.

#### Scenario: PyPI responde dentro do timeout
- **WHEN** PyPI responde em menos de 5 segundos
- **THEN** sistema processa resposta normalmente

#### Scenario: PyPI não responde dentro do timeout
- **WHEN** PyPI não responde em 5 segundos
- **THEN** sistema aborta verificação silenciosamente e continua execução

### Requirement: Notificação visual

O sistema DEVE exibir notificação de update de forma visualmente destacada mas não intrusiva.

#### Scenario: Exibição de notificação
- **WHEN** há update disponível e notificação não está suprimida
- **THEN** sistema exibe painel Rich com versão atual, versão disponível e comando de upgrade

### Requirement: Abstração de cliente HTTP

O sistema DEVE abstrair o cliente HTTP para permitir troca futura de implementação.

#### Scenario: Uso da abstração
- **WHEN** sistema precisa fazer request HTTP
- **THEN** sistema usa interface HttpClient que pode ter múltiplas implementações

#### Scenario: Implementação padrão
- **WHEN** nenhuma implementação específica é configurada
- **THEN** sistema usa UrllibClient (stdlib, zero dependências)
