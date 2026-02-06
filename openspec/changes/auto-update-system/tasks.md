## 1. Setup do módulo

- [x] 1.1 Criar estrutura de diretórios `src/code_reviewer/updater/`
- [x] 1.2 Criar `updater/__init__.py` com exports públicos

## 2. HTTP Client (abstração)

- [x] 2.1 Criar `updater/http_client.py` com Protocol HttpClient
- [x] 2.2 Implementar UrllibClient com método get(url, timeout)
- [x] 2.3 Criar factory function get_http_client()

## 3. Version Check

- [x] 3.1 Criar `updater/version_check.py`
- [x] 3.2 Implementar função get_latest_version() que consulta PyPI
- [x] 3.3 Implementar lógica de cache em ~/.cache/airev/update-check.json
- [x] 3.4 Implementar check_for_update() que retorna UpdateInfo | None
- [x] 3.5 Implementar comparação de versões (packaging.version ou manual)

## 4. Notifier

- [x] 4.1 Criar `updater/notifier.py`
- [x] 4.2 Implementar notify_update() usando Rich Panel
- [x] 4.3 Incluir versão atual, versão disponível e comandos de upgrade

## 5. Comando Upgrade

- [x] 5.1 Implementar detect_installer() para identificar pipx vs pip
- [x] 5.2 Implementar run_upgrade() que executa o comando apropriado
- [x] 5.3 Adicionar comando `upgrade` no cli.py

## 6. Integração no CLI

- [x] 6.1 Importar e chamar check de update no main() do cli.py
- [x] 6.2 Implementar lógica de opt-out via CODE_REVIEWER_NO_UPDATE_CHECK
- [x] 6.3 Suprimir notificação quando --json-output está ativo
- [x] 6.4 Garantir que falhas no check não bloqueiam execução

## 7. Testes (auto-update)

- [x] 7.1 Testes para http_client (mock de urllib)
- [x] 7.2 Testes para version_check (cache, comparação)
- [x] 7.3 Testes para notifier (output formatado)
- [x] 7.4 Testes para detect_installer
- [x] 7.5 Testes de integração no CLI

## 8. Release Automation - Configuração

- [x] 8.1 Adicionar python-semantic-release às dependências dev
- [x] 8.2 Configurar pyproject.toml para versão dinâmica (ler de __init__.py)
- [x] 8.3 Adicionar configuração [tool.semantic_release] no pyproject.toml
- [x] 8.4 Configurar commit_parser para Conventional Commits

## 9. Release Automation - GitHub Actions

- [x] 9.1 Criar .github/workflows/release.yml
- [x] 9.2 Configurar trigger on push to main
- [x] 9.3 Adicionar steps: checkout, setup-python, install deps
- [x] 9.4 Adicionar step semantic-release publish
- [x] 9.5 Documentar secrets necessários (PYPI_TOKEN, GH_TOKEN)

## 10. Release Automation - Makefile

- [x] 10.1 Adicionar target `release-dry-run` (preview sem aplicar)
- [x] 10.2 Adicionar target `release` (execução local)
- [x] 10.3 Atualizar help do Makefile

## 11. Documentação

- [x] 11.1 Criar/atualizar README com instruções de instalação via pipx
- [x] 11.2 Documentar Conventional Commits para contribuidores
- [x] 11.3 Adicionar CONTRIBUTING.md com guia de commits
