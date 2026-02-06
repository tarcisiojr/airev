## Why

A aplicação precisa ser distribuível para que usuários possam instalá-la em seus computadores. Com múltiplas instalações, é necessário um sistema de auto-update para garantir que todos estejam sempre na versão mais recente, seguindo o padrão de CLIs modernas como Claude Code, GitHub Copilot CLI e Gemini CLI.

Além disso, o processo de release precisa ser automatizado para garantir versionamento consistente, geração de changelog e publicação no PyPI de forma padronizada.

## What Changes

- Adicionar módulo `updater/` com sistema de verificação de versão
- Implementar check de versão no startup do CLI (com cache de 1 hora)
- Adicionar notificação visual quando há atualização disponível
- Criar comando `airev upgrade` para facilitar atualização
- Abstrair cliente HTTP para permitir troca futura (urllib → httpx)
- Suportar opt-out via variável de ambiente
- Configurar python-semantic-release para automação de releases
- Adotar Conventional Commits para mensagens de commit
- Configurar GitHub Actions para CI/CD de releases
- Gerar CHANGELOG.md automaticamente

## Capabilities

### New Capabilities

- `auto-update`: Sistema de verificação automática de versão e notificação de atualizações. Inclui check contra PyPI, cache local, notificação visual e comando de upgrade.
- `release-automation`: Automação de releases com python-semantic-release, Conventional Commits, geração de CHANGELOG e publicação automática no PyPI via GitHub Actions.

### Modified Capabilities

- `cli`: Integração do check de versão no startup e adição do comando `upgrade`. Supressão de notificação quando `--json-output` está ativo.

## Impact

- **Novo módulo**: `src/code_reviewer/updater/` com 4 arquivos
- **CLI**: Modificação em `cli.py` para integrar check e novo comando
- **Dependências runtime**: Nenhuma nova (usa urllib da stdlib)
- **Dependências dev**: python-semantic-release
- **Filesystem**: Novo diretório de cache em `~/.cache/airev/`
- **Network**: Requests ao PyPI (https://pypi.org/pypi/airev/json)
- **Ambiente**: Nova env var `CODE_REVIEWER_NO_UPDATE_CHECK`
- **CI/CD**: Novo workflow GitHub Actions para release automático
- **Configs**: pyproject.toml (semantic-release), .github/workflows/release.yml
- **Commits**: Adoção de Conventional Commits (feat:, fix:, etc.)
