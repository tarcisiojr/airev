## ADDED Requirements

### Requirement: Cache é invalidado após upgrade
O sistema SHALL limpar o cache de verificação de versão (`~/.cache/airev/update-check.json`) após executar qualquer tentativa de upgrade, independente do resultado.

#### Scenario: Cache limpo após upgrade bem-sucedido
- **WHEN** usuário executa `airev upgrade` e a atualização é concluída
- **THEN** o arquivo de cache de versão é removido

#### Scenario: Cache limpo após upgrade sem mudança
- **WHEN** usuário executa `airev upgrade` mas já está na versão mais recente
- **THEN** o arquivo de cache de versão é removido

#### Scenario: Cache limpo após falha de upgrade
- **WHEN** usuário executa `airev upgrade` e o comando falha
- **THEN** o arquivo de cache de versão é removido

### Requirement: Verificação de versão real após upgrade
O sistema SHALL verificar a versão efetivamente instalada após executar o comando de upgrade, consultando o instalador (pipx ou pip).

#### Scenario: Detectar atualização real
- **WHEN** upgrade é executado e versão instalada muda de 1.0.0 para 1.1.0
- **THEN** sistema reporta "Atualizado de 1.0.0 para 1.1.0"

#### Scenario: Detectar quando upgrade não teve efeito
- **WHEN** upgrade é executado mas versão instalada permanece 1.0.0
- **THEN** sistema reporta que já está na versão mais recente ou que upgrade falhou

### Requirement: Feedback preciso de atualização
O sistema SHALL fornecer mensagens de feedback que refletem o estado real da atualização.

#### Scenario: Já na versão mais recente
- **WHEN** versão local é igual à versão mais recente no PyPI
- **THEN** sistema exibe "Você já está na versão mais recente (X.Y.Z)"

#### Scenario: Atualização disponível e executada
- **WHEN** existe versão mais recente e upgrade é executado com sucesso
- **THEN** sistema exibe "Atualizado de X.Y.Z para A.B.C"

#### Scenario: Atualização disponível mas falhou
- **WHEN** existe versão mais recente mas upgrade falha ou não tem efeito
- **THEN** sistema exibe mensagem de erro com instruções para atualização manual
