# airev

CLI para revisão de código automatizada com IA. Analisa diffs de branches Git e identifica problemas de segurança, performance, bugs e vazamentos de recursos.

## Funcionalidades

- **Análise de diff inteligente**: Compara sua branch com a branch base e analisa apenas o código modificado
- **Context backtracking**: Identifica automaticamente funções que chamam ou são chamadas pelo código modificado
- **Análise estática determinística**: Complementa a IA com linters locais (ruff/pyflakes para Python, tsc/eslint para JS/TS, go build para Go) — variáveis não declaradas e erros de compilação são detectados com 100% de confiança
- **Modo thorough**: Uma passada de IA dedicada por categoria (segurança, performance, bugs) para máxima cobertura
- **Múltiplos runners de IA**: Suporte a Gemini CLI, GitHub Copilot CLI e Claude Code CLI
- **Output estruturado**: Resultados em terminal colorido ou JSON para integração com CI/CD
- **Internacionalização**: Suporte a português (pt-br) e inglês (en)
- **Categorização de findings**: Severidade (CRITICAL, WARNING, INFO) e categoria (security, performance, bug, resource-leak)

## Instalação

### Requisitos

- Python 3.10+
- Git
- Um CLI de IA instalado:
  - [Gemini CLI](https://github.com/google-gemini/gemini-cli) (padrão)
  - [GitHub Copilot CLI](https://github.com/github/copilot-cli)
  - [Claude Code CLI](https://docs.claude.com/en/docs/claude-code)

### Via pipx (Recomendado)

```bash
# Instala o pipx se ainda não tiver
pip install pipx
pipx ensurepath

# Instala o airev
pipx install airev
```

### Via pip

```bash
pip install airev
```

### Desenvolvimento local

```bash
# Clone o repositório
git clone https://github.com/tarcisiojr/airev.git
cd airev

# Instala em modo desenvolvimento
pip install -e ".[dev]"
```

## Atualização

O airev verifica automaticamente por novas versões e notifica quando há atualizações disponíveis.

```bash
# Atualiza para a versão mais recente
airev upgrade

# Ou manualmente
pipx upgrade airev
# ou
pip install --upgrade airev
```

Para desabilitar a verificação automática:
```bash
export AIREV_NO_UPDATE_CHECK=1
```

## Uso

### Comando básico

```bash
# Analisa a branch atual contra main
airev review --base main

# Analisa contra develop usando Copilot
airev review --base develop --runner copilot

# Output em JSON para CI/CD
airev review --base main --json-output

# Modo silencioso (sem animações)
airev review --base main --no-progress

# Em inglês
airev review --base main --lang en
```

### Opções do comando `review`

| Opção | Descrição |
|-------|-----------|
| `--base`, `-b` | Branch base para comparação (obrigatório) |
| `--runner`, `-r` | Runner de IA: `gemini` (padrão), `copilot` ou `claude` |
| `--json-output`, `-j` | Retorna resultado em JSON |
| `--workdir`, `-w` | Diretório do repositório (padrão: atual) |
| `--no-progress` | Desabilita animações (modo CI) |
| `--progress` | Força animações mesmo em CI |
| `--lang`, `-l` | Idioma: `pt-br` (padrão) ou `en` |
| `--min-confidence`, `-c` | Exibe apenas findings com confidence >= N (padrão: 7). O CLI informa quantos findings foram ocultados pelo filtro |
| `--thorough`, `-T` | Análise profunda: uma passada de IA por categoria. Mais lento, maior cobertura |

### Listar runners disponíveis

```bash
airev runners
```

## Runners de IA

### Gemini CLI (padrão)

Instale o Gemini CLI:

```bash
npm install -g @anthropic/gemini-cli
# ou
brew install gemini-cli
```

### GitHub Copilot CLI

Instale o Copilot CLI standalone:

```bash
npm install -g @github/copilot-cli
# ou
brew install github/gh/copilot-cli
# ou
winget install GitHub.CopilotCLI
```

### Claude Code CLI

Instale o Claude Code:

```bash
npm install -g @anthropic-ai/claude-code
```

Use com:

```bash
airev review --base main --runner claude
```

## Output

### Terminal

O output no terminal inclui:

- Lista de arquivos modificados com estatísticas de linhas
- Dependências identificadas (callers/callees)
- Findings categorizados por severidade com cores
- Resumo final com contagem por tipo

### JSON

Com `--json-output`, o resultado segue a estrutura:

```json
{
  "branch": "feature/x",
  "base": "main",
  "files_analyzed": 5,
  "findings": [
    {
      "file": "src/auth.py",
      "line": 42,
      "severity": "CRITICAL",
      "category": "security",
      "title": "SQL Injection",
      "description": "Query concatenada sem sanitização",
      "suggestion": "Use prepared statements"
    }
  ],
  "summary": {
    "total": 3,
    "critical": 1,
    "warning": 2,
    "info": 0
  }
}
```

## Integração com CI/CD

### GitHub Actions

```yaml
- name: Code Review
  run: |
    pip install airev
    airev review --base main --no-progress --json-output > review.json

- name: Check Critical Findings
  run: |
    CRITICAL=$(jq '.summary.critical' review.json)
    if [ "$CRITICAL" -gt 0 ]; then
      echo "Found $CRITICAL critical issues!"
      exit 1
    fi
```

## Telemetria

O airev coleta dados anônimos de uso para ajudar a entender como a ferramenta é utilizada e melhorar a experiência. A telemetria é **habilitada por padrão** e pode ser desabilitada a qualquer momento.

### O que é coletado

Apenas metadados anônimos e não-sensíveis:

- Runner utilizado (gemini, copilot)
- Flags de configuração (valores booleanos)
- Contagens numéricas (arquivos analisados, findings por severidade)
- Duração do review
- Tipo de erro em caso de falha (enum fixo, sem mensagens de erro)
- Versão do airev

### O que **não** é coletado

- Código-fonte ou diffs
- Nomes de branches ou caminhos de arquivo
- Descrições de PR ou mensagens de erro
- Qualquer informação que identifique o projeto analisado

### Identidade

Um UUID v4 aleatório é gerado na primeira execução e salvo em `~/.cache/airev/anonymous_id`. Este ID é completamente anônimo e não pode ser associado a nenhum dado pessoal.

### Opt-out

Para desabilitar a telemetria:

```bash
export AIREV_NO_TELEMETRY=1
```

Quando desabilitada, nenhum evento é enviado, nenhuma conexão de rede é feita, e o SDK de analytics não é sequer importado.

## Desenvolvimento

### Executar testes

```bash
pytest
```

### Executar com cobertura

```bash
pytest --cov=code_reviewer
```

### Verificar código

```bash
python -m py_compile src/code_reviewer/*.py
```

## Arquitetura

```
src/code_reviewer/
├── cli.py              # Entry point e comandos Click
├── diff_parser.py      # Parser de git diff
├── context_builder.py  # Backtracking de dependências
├── prompt_builder.py   # Construção do prompt para IA
├── static_analysis.py  # Camada determinística (ruff, tsc, eslint, go build)
├── response_parser.py  # Parser da resposta da IA
├── models.py           # Modelos Pydantic
├── formatters/
│   ├── terminal.py     # Formatação colorida com rich
│   └── progress.py     # Reporter de progresso
├── analytics/
│   ├── __init__.py     # API pública: track_event(), shutdown_analytics()
│   ├── client.py       # Client PostHog com lazy init e flush assíncrono
│   └── identity.py     # UUID anônimo persistido
├── runners/
│   ├── base.py         # Interface AIRunner
│   ├── gemini.py       # Runner Gemini CLI
│   └── copilot.py      # Runner Copilot CLI
├── i18n/               # Sistema de internacionalização
├── locales/            # Arquivos de tradução (YAML)
└── prompts/            # Templates de prompt
```

## Licença

MIT
