## 1. Dependências

- [x] 1.1 Adicionar `prompt_toolkit` ao `pyproject.toml` em `dependencies`

## 2. Flags CLI

- [x] 2.1 Adicionar flag `--description` / `-d` ao comando `review` em `cli.py`
- [x] 2.2 Adicionar flag `--no-interactive` ao comando `review` em `cli.py`
- [x] 2.3 Passar flags para o fluxo de review

## 3. Leitura de Stdin

- [x] 3.1 Implementar leitura de stdin quando `-d -` é fornecido
- [x] 3.2 Detectar stdin vazio (não bloquear aguardando input)
- [x] 3.3 Aplicar limite de 2000 caracteres ao conteúdo de stdin

## 4. Módulo de Input Interativo

- [x] 4.1 Criar módulo `description_input.py` com função para captura de descrição
- [x] 4.2 Implementar lógica de detecção TTY para modo interativo
- [x] 4.3 Implementar input multi-linha com `prompt_toolkit` e bracketed paste
- [x] 4.4 Implementar tratamento de Ctrl+C (continuar sem descrição)
- [x] 4.5 Implementar limite de 2000 caracteres com aviso de truncamento

## 5. Integração no CLI

- [x] 5.1 Adicionar chamada ao prompt interativo após exibir arquivos modificados
- [x] 5.2 Implementar lógica de decisão: flag fornecida vs stdin vs interativo vs pular
- [x] 5.3 Passar descrição capturada para `build_prompt`

## 6. Prompt Builder

- [x] 6.1 Adicionar parâmetro `description` à função `build_prompt`
- [x] 6.2 Criar função `get_description_section` para formatar seção de descrição
- [x] 6.3 Adicionar placeholder `{description}` ao template `review_system.md`
- [x] 6.4 Implementar substituição condicional (seção vazia se sem descrição)

## 7. Testes

- [x] 7.1 Testes para parsing das novas flags CLI
- [x] 7.2 Testes para leitura de stdin (`-d -`)
- [x] 7.3 Testes para lógica de decisão do modo interativo
- [x] 7.4 Testes para truncamento de descrição
- [x] 7.5 Testes para formatação da seção de descrição no prompt
- [x] 7.6 Testes para prompt sem descrição (seção não aparece)
