## Context

O sistema de code review usa um prompt (`review_system.md`) que instrui a LLM a analisar apenas linhas marcadas com `+` no diff. Porém, quando o diff mostra código parcial (ex: abertura de bloco `if (x) {` sem o fechamento `}`), a LLM pode erroneamente reportar erro de sintaxe, pois não visualiza o contexto completo.

O prompt atual já inclui o contexto completo dos arquivos modificados na seção "ARQUIVOS MODIFICADOS", mas não instrui explicitamente a LLM a usá-lo para validar questões de sintaxe antes de reportar.

## Goals / Non-Goals

**Goals:**
- Eliminar falsos positivos de erros de sintaxe causados por visualização parcial do diff
- Instruir explicitamente a LLM a cruzar informações do diff com o arquivo completo
- Manter o foco da análise apenas no código alterado (linhas com `+`)

**Non-Goals:**
- Mudar a estrutura geral do prompt ou formato de saída
- Adicionar novas categorias de análise
- Modificar o parsing de resposta ou diff

## Decisions

### 1. Adicionar seção "AVISOS IMPORTANTES" no prompt

**Decisão**: Criar uma nova seção no prompt com avisos explícitos sobre falsos positivos.

**Racional**: Instruções claras e destacadas são mais eficazes para guiar o comportamento da LLM do que regras genéricas.

**Alternativas consideradas**:
- Adicionar nas regras existentes → Menos visibilidade, pode ser ignorado
- Usar exemplos de falsos positivos → Muito verboso, aumenta token count

### 2. Texto da instrução anti-falso-positivo

**Decisão**: Adicionar instrução específica:
> "IMPORTANTE: O diff mostra apenas as linhas alteradas. Código aparentemente incompleto (blocos abertos, imports parciais) pode estar completo no arquivo original. SEMPRE consulte a seção 'ARQUIVOS MODIFICADOS' antes de reportar erros de sintaxe ou código incompleto."

**Racional**: Explica o problema (diff parcial), a causa (código aparentemente incompleto) e a solução (consultar arquivo completo).

### 3. Posicionamento no prompt

**Decisão**: Colocar o aviso logo após as "REGRAS IMPORTANTES", antes do "FOCO DA ANÁLISE".

**Racional**: Após as regras principais mas antes dos detalhes técnicos, garantindo que seja lido mas não quebre o fluxo lógico.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| LLM ignorar a nova instrução | Usar formatação destacada (IMPORTANTE, caixa alta) e posicionamento estratégico |
| Aumento de tokens no prompt | Instrução é curta (~50 palavras), impacto mínimo |
| LLM deixar de reportar erros reais de sintaxe | Instrução pede para "consultar" o arquivo, não para "ignorar" erros |
