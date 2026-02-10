## Why

A IA vê **o que** mudou no código, mas não sabe **por quê**. A descrição do PR/MR traz contexto sobre a intenção do desenvolvedor, permitindo reviews mais precisos e contextualizados. Isso é especialmente útil em pipelines de CI onde a descrição já existe no PR.

## What Changes

- Adiciona flag `--description` / `-d` para informar descrição das alterações via linha de comando
- Adiciona flag `--no-interactive` para desabilitar prompts interativos (modo CI)
- Em modo interativo (TTY), pergunta ao usuário se quer adicionar descrição após mostrar os arquivos modificados
- Suporta input multi-linha via `prompt_toolkit` com bracketed paste (permite colar Markdown)
- Inclui a descrição no prompt enviado à IA como contexto adicional

## Capabilities

### New Capabilities

- `description-input`: Captura da descrição das alterações via flag CLI ou prompt interativo com suporte a multi-linha

### Modified Capabilities

- `prompt-building`: Incluir seção de descrição das alterações no prompt enviado à IA

## Impact

- **CLI**: Novas flags `--description`/`-d` e `--no-interactive` no comando `review`
- **Dependências**: Adicionar `prompt_toolkit` ao `pyproject.toml`
- **Prompt template**: Novo placeholder `{description}` no `review_system.md`
- **UX**: Novo fluxo interativo após exibição do diff
