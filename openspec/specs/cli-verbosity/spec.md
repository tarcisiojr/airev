## ADDED Requirements

### Requirement: Exibir spinner animado durante etapas do pipeline
O sistema SHALL exibir um spinner animado com mensagem de status durante cada etapa do pipeline de análise.

#### Scenario: Spinner durante parsing do diff
- **WHEN** o sistema está executando o parsing do diff
- **THEN** o terminal exibe um spinner com a mensagem "Analisando diff..."

#### Scenario: Spinner durante construção de contexto
- **WHEN** o sistema está construindo o contexto (backtracking)
- **THEN** o terminal exibe um spinner com a mensagem "Construindo contexto..."

#### Scenario: Spinner durante execução da IA
- **WHEN** o sistema está aguardando resposta do runner de IA
- **THEN** o terminal exibe um spinner com a mensagem "Executando análise com {runner}..."

#### Scenario: Spinner durante parsing da resposta
- **WHEN** o sistema está parseando a resposta da IA
- **THEN** o terminal exibe um spinner com a mensagem "Processando resposta..."

### Requirement: Desabilitar animações com flag --no-progress
O sistema SHALL aceitar a flag `--no-progress` para desabilitar todas as animações e spinners.

#### Scenario: Flag --no-progress desabilita spinners
- **WHEN** o usuário executa `airev review --base main --no-progress`
- **THEN** o terminal exibe mensagens de status simples em vez de spinners animados

#### Scenario: Mensagens de progresso em modo texto
- **WHEN** o sistema está em modo --no-progress durante o parsing do diff
- **THEN** o terminal exibe "→ Analisando diff..." como texto simples

### Requirement: Auto-detectar ambiente CI
O sistema SHALL detectar automaticamente quando está rodando em ambiente CI ou pipe e desabilitar animações.

#### Scenario: Detectar não-TTY
- **WHEN** stdout não é um TTY (pipe ou redirecionamento)
- **THEN** o sistema desabilita animações automaticamente

#### Scenario: Detectar variável CI
- **WHEN** a variável de ambiente CI, GITLAB_CI, GITHUB_ACTIONS ou JENKINS_URL está definida
- **THEN** o sistema desabilita animações automaticamente

#### Scenario: Forçar animação com --progress
- **WHEN** o usuário passa --progress explicitamente em ambiente CI
- **THEN** o sistema habilita animações mesmo em CI

### Requirement: Exibir lista de arquivos modificados
O sistema SHALL exibir a lista de arquivos modificados com contagem de linhas após o parsing do diff.

#### Scenario: Lista de arquivos com linhas
- **WHEN** o diff contém 3 arquivos modificados
- **THEN** o terminal exibe cada arquivo com contagem de linhas adicionadas/removidas: "  payment.py (+15, -3)"

#### Scenario: Resumo do diff
- **WHEN** o parsing do diff termina
- **THEN** o terminal exibe "Arquivos: 3 | Linhas: +45, -12"

### Requirement: Exibir dependências durante backtracking
O sistema SHALL exibir os arquivos encontrados durante o backtracking (callers e callees).

#### Scenario: Callers encontrados
- **WHEN** o backtracking encontra 2 arquivos que chamam a função modificada
- **THEN** o terminal exibe "  Callers: checkout.py, api.py"

#### Scenario: Callees encontrados
- **WHEN** o backtracking encontra 1 função chamada pelo código modificado
- **THEN** o terminal exibe "  Callees: validate_card() em utils.py"

#### Scenario: Nenhuma dependência
- **WHEN** o backtracking não encontra callers nem callees
- **THEN** o terminal exibe "  Sem dependências encontradas"

### Requirement: Exibir estatísticas de tempo ao final
O sistema SHALL exibir estatísticas de tempo de execução ao final da análise.

#### Scenario: Tempo total exibido
- **WHEN** a análise termina com sucesso
- **THEN** o terminal exibe "Tempo total: X.Xs" no resumo

#### Scenario: Tempo por etapa em modo verbose
- **WHEN** a análise termina e --verbose foi passado
- **THEN** o terminal exibe tempo de cada etapa: diff, contexto, IA, parsing
