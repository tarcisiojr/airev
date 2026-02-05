## 1. Setup do projeto

- [x] 1.1 Criar `pyproject.toml` com metadata, dependências (click, pydantic) e entry point `code-reviewer`
- [x] 1.2 Criar estrutura de diretórios: `src/code_reviewer/`, `tests/`, `src/code_reviewer/runners/`, `src/code_reviewer/formatters/`, `src/code_reviewer/prompts/`
- [x] 1.3 Criar `src/code_reviewer/__init__.py` e demais `__init__.py`

## 2. Models (Pydantic)

- [x] 2.1 Criar `src/code_reviewer/models.py` com modelos: `DiffHunk`, `DiffFile`, `FunctionRef`, `ContextGraph`, `Finding`, `ReviewSummary`, `ReviewResult`

## 3. Diff Parser

- [x] 3.1 Criar `src/code_reviewer/diff_parser.py` com função que executa `git diff <base>...HEAD` via subprocess
- [x] 3.2 Implementar parsing do diff: extrair arquivos modificados, hunk headers (nomes de funções) e linhas adicionadas/removidas
- [x] 3.3 Implementar filtro de arquivos irrelevantes (lock files, migrations, arquivos gerados)
- [x] 3.4 Criar testes em `tests/test_diff_parser.py` com diffs de exemplo

## 4. Context Builder (Backtracking)

- [x] 4.1 Criar `src/code_reviewer/context_builder.py` com função para rastrear callers via grep
- [x] 4.2 Implementar rastreamento de callees: identificar novos símbolos nas linhas adicionadas e buscar definições
- [x] 4.3 Implementar leitura do conteúdo completo dos arquivos modificados
- [x] 4.4 Implementar filtro de diretórios excluídos (node_modules, venv, .git, __pycache__, etc.)
- [x] 4.5 Implementar limite de referências (max 5 por símbolo, max 10 linhas de contexto)
- [x] 4.6 Criar testes em `tests/test_context_builder.py`

## 5. Prompt Builder

- [x] 5.1 Criar `src/code_reviewer/prompts/review_system.md` com template do system prompt incluindo placeholders e schema JSON
- [x] 5.2 Criar `src/code_reviewer/prompt_builder.py` com função que carrega template e substitui placeholders ({diff}, {context}, {references}, {json_schema})
- [x] 5.3 Criar testes em `tests/test_prompt_builder.py`

## 6. AI Runners

- [x] 6.1 Criar `src/code_reviewer/runners/base.py` com Protocol `AIRunner` definindo interface `run(prompt, workdir) -> str`
- [x] 6.2 Criar `src/code_reviewer/runners/gemini.py` com `GeminiCLIRunner` que executa via subprocess
- [x] 6.3 Criar `src/code_reviewer/runners/copilot.py` com `CopilotCLIRunner` que executa via subprocess
- [x] 6.4 Implementar verificação de disponibilidade do CLI no PATH em cada runner
- [x] 6.5 Criar registry de runners em `src/code_reviewer/runners/__init__.py` para lookup por nome

## 7. Response Parser

- [x] 7.1 Criar `src/code_reviewer/response_parser.py` com cadeia de parsing: json.loads → extrair de markdown → regex → fallback raw
- [x] 7.2 Implementar validação contra modelos Pydantic com tratamento de campos ausentes e valores inválidos
- [x] 7.3 Criar testes em `tests/test_response_parser.py` com cenários: JSON válido, JSON em markdown, JSON parcial, texto raw

## 8. Terminal Formatter

- [x] 8.1 Criar `src/code_reviewer/formatters/terminal.py` com renderização colorida: CRITICAL (vermelho), WARNING (amarelo), INFO (azul)
- [x] 8.2 Implementar agrupamento de findings por arquivo
- [x] 8.3 Implementar header com info da análise (branch, base, arquivos) e resumo final com contadores
- [x] 8.4 Criar testes em `tests/test_terminal_formatter.py`

## 9. CLI Entry Point

- [x] 9.1 Criar `src/code_reviewer/cli.py` com comando `review` usando click: flags `--base`, `--runner`, `--json-output`
- [x] 9.2 Integrar todo o pipeline: diff_parser → context_builder → prompt_builder → ai_runner → response_parser → terminal formatter
- [x] 9.3 Implementar flag `--json-output` para retornar JSON raw em vez de formatação terminal (útil para integrações)

## 10. Validação e documentação

- [x] 10.1 Rodar pipeline completo localmente contra um repositório de teste
- [x] 10.2 Verificar que `pip install .` funciona e o comando `code-reviewer review --base main` está disponível
