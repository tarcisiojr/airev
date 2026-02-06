## ADDED Requirements

### Requirement: Arquivos de localização incluídos no pacote distribuído

O sistema de build SHALL incluir os arquivos `locales/*.yaml` no pacote distribuído para que o módulo i18n funcione corretamente quando instalado via pip/pipx.

#### Scenario: Instalação via pip inclui arquivos de tradução
- **WHEN** o pacote é instalado via `pip install airev` ou `pipx install airev`
- **THEN** os arquivos `locales/pt-br.yaml` e `locales/en.yaml` estão presentes no diretório de instalação

#### Scenario: Mensagens aparecem traduzidas após instalação
- **WHEN** o usuário executa `airev review --base main` após instalar via pip/pipx
- **THEN** as mensagens aparecem no idioma configurado (ex: "Analisando: feature → main") ao invés das chaves brutas (ex: "cli.analyzing")
