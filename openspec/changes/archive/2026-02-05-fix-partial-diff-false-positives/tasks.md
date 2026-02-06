## 1. Atualizar Prompt de Revisão

- [x] 1.1 Adicionar seção "AVISO IMPORTANTE" no arquivo `src/code_reviewer/prompts/review_system.md` após "REGRAS IMPORTANTES"
- [x] 1.2 Incluir texto anti-falso-positivo explicando que o diff é parcial e que a LLM deve consultar "ARQUIVOS MODIFICADOS" antes de reportar erros de sintaxe

## 2. Atualizar Spec Principal

- [x] 2.1 Sincronizar delta spec de `prompt-building` para `openspec/specs/prompt-building/spec.md`

## 3. Validação

- [x] 3.1 Executar testes existentes para garantir que a mudança não quebrou nada
- [x] 3.2 Testar manualmente com um diff parcial para verificar que falsos positivos de sintaxe foram reduzidos
