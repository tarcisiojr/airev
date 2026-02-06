## ADDED Requirements

### Requirement: Conventional Commits

O projeto DEVE adotar Conventional Commits como padrão para mensagens de commit.

#### Scenario: Commit de nova funcionalidade
- **WHEN** desenvolvedor faz commit com prefixo `feat:`
- **THEN** semantic-release identifica como minor bump

#### Scenario: Commit de correção
- **WHEN** desenvolvedor faz commit com prefixo `fix:`
- **THEN** semantic-release identifica como patch bump

#### Scenario: Commit com breaking change
- **WHEN** desenvolvedor faz commit com prefixo `feat!:` ou `fix!:`
- **THEN** semantic-release identifica como major bump

#### Scenario: Commit sem prefixo relevante
- **WHEN** desenvolvedor faz commit com prefixo `chore:`, `docs:`, `style:`, `refactor:`, `test:`
- **THEN** semantic-release não gera novo release

### Requirement: Versionamento automático

O sistema DEVE determinar automaticamente a próxima versão baseado nos commits.

#### Scenario: Análise de commits desde última tag
- **WHEN** CI executa semantic-release em push para main
- **THEN** sistema analisa todos os commits desde a última tag de versão

#### Scenario: Bump de versão calculado
- **WHEN** existem commits com feat: e fix: desde última tag
- **THEN** sistema aplica o bump mais significativo (feat > fix)

#### Scenario: Nenhum commit relevante
- **WHEN** todos os commits são chore:, docs:, etc.
- **THEN** sistema não cria novo release

### Requirement: Atualização automática de __version__

O sistema DEVE atualizar `__init__.py` com a nova versão automaticamente.

#### Scenario: Bump aplicado ao código
- **WHEN** semantic-release determina nova versão 0.2.0
- **THEN** `src/code_reviewer/__init__.py` é atualizado com `__version__ = "0.2.0"`

### Requirement: Geração de CHANGELOG

O sistema DEVE gerar e manter CHANGELOG.md automaticamente.

#### Scenario: Novo release adiciona entrada
- **WHEN** nova versão 0.2.0 é criada
- **THEN** CHANGELOG.md recebe nova seção com lista de mudanças

#### Scenario: Agrupamento por tipo
- **WHEN** CHANGELOG é gerado
- **THEN** mudanças são agrupadas por tipo (Features, Bug Fixes, etc.)

### Requirement: Criação de tag Git

O sistema DEVE criar tag Git para cada release.

#### Scenario: Tag criada automaticamente
- **WHEN** nova versão 0.2.0 é determinada
- **THEN** sistema cria tag `v0.2.0` no repositório

#### Scenario: Tag assinada
- **WHEN** tag é criada
- **THEN** tag é push para o repositório remoto

### Requirement: Publicação automática no PyPI

O sistema DEVE publicar automaticamente no PyPI quando há novo release.

#### Scenario: Build e upload
- **WHEN** nova versão é criada
- **THEN** sistema faz build do pacote e upload para PyPI

#### Scenario: Credenciais via secrets
- **WHEN** upload para PyPI é executado
- **THEN** sistema usa PYPI_TOKEN configurado nos GitHub Secrets

### Requirement: CI/CD via GitHub Actions

O sistema DEVE executar release automation via GitHub Actions.

#### Scenario: Trigger em push para main
- **WHEN** push é feito para branch main
- **THEN** workflow de release é executado

#### Scenario: Workflow idempotente
- **WHEN** não há commits relevantes desde último release
- **THEN** workflow termina sem criar novo release

### Requirement: Comandos locais para release

O sistema DEVE fornecer comandos Makefile para releases manuais e dry-run.

#### Scenario: Dry-run local
- **WHEN** desenvolvedor executa `make release-dry-run`
- **THEN** sistema mostra qual seria a próxima versão sem aplicar mudanças

#### Scenario: Release manual
- **WHEN** desenvolvedor executa `make release`
- **THEN** sistema executa semantic-release localmente (requer credenciais)
