## 1. Correção de Configuração

- [x] 1.1 Adicionar `locales/*.yaml` ao package-data em `pyproject.toml`

## 2. Validação

- [x] 2.1 Executar build do pacote (`python -m build`)
- [x] 2.2 Verificar se os arquivos de locale estão no wheel gerado
- [x] 2.3 Testar instalação em ambiente limpo (pipx install --force)
- [x] 2.4 Confirmar que mensagens aparecem traduzidas ao executar `airev review`
