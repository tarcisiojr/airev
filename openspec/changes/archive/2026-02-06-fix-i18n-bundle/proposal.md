## Why

As mensagens de internacionalização aparecem como chaves brutas (`cli.analyzing`, `progress.modified_files`) ao invés do texto traduzido quando o CLI é instalado via pip/pipx em outro computador. Os arquivos YAML de localização (`locales/*.yaml`) não estão sendo incluídos no bundle de distribuição do pacote.

## What Changes

- Adicionar os arquivos `locales/*.yaml` ao `package-data` no `pyproject.toml`
- Atualmente apenas `prompts/*.md` está configurado, faltando os arquivos de tradução

## Capabilities

### New Capabilities

Nenhuma nova capability será criada.

### Modified Capabilities

Nenhuma capability existente precisa de alteração de spec - esta é uma correção de configuração de empacotamento.

## Impact

- **Arquivo afetado**: `pyproject.toml` (seção `[tool.setuptools.package-data]`)
- **Comportamento após fix**: Os arquivos de tradução serão incluídos no pacote distribuído, permitindo que o i18n funcione corretamente em instalações via pip/pipx
- **Teste de validação**: Instalar o pacote em ambiente limpo e verificar se as mensagens aparecem traduzidas
