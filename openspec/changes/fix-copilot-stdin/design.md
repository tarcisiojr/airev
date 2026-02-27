## Context

O `CopilotCLIRunner` atualmente passa o prompt inteiro como argumento de linha de comando via flag `-p`. Quando o diff analisado é grande (muitos arquivos modificados, contexto extenso, muitas referências), o prompt resultante excede o limite `ARG_MAX` do sistema operacional (~256KB no macOS), causando `[Errno 7] Argument list too long`.

O runner do Gemini (`GeminiCLIRunner`) já passa o prompt via stdin (`input=prompt` no `subprocess.run`), evitando esse problema. A issue #1046 do repositório copilot-cli confirmou que stdin é suportado desde Janeiro/2026.

## Goals / Non-Goals

**Goals:**
- Eliminar o erro `Errno 7` ao analisar changes grandes com o runner copilot
- Passar o prompt via stdin, alinhando com o padrão já usado pelo runner Gemini

**Non-Goals:**
- Adicionar validação/truncamento genérico de tamanho de prompt (pode ser feito em change futura)
- Alterar flags do copilot CLI (`--yolo`, `--silent`) — essas permanecem como estão
- Suportar a combinação stdin + `-p` simultaneamente (issue #683, não resolvida)

## Decisions

### Decisão 1: Prompt via stdin em vez de argumento CLI

**Escolha**: Passar o prompt via `input=prompt` no `subprocess.run`, removendo `-p prompt` da lista de argumentos.

**Alternativas consideradas:**
1. **Arquivo temporário**: Escrever prompt em arquivo temp e passar caminho via `-p @file`. Mais complexo, requer cleanup, e o copilot CLI não documenta leitura de arquivo via `-p`.
2. **Truncar prompt**: Limitar o tamanho do prompt para caber em ARG_MAX. Perderia contexto valioso da análise.
3. **stdin com `-p ""`**: Usar `-p ""` junto com stdin como demonstrado na issue #1046. Adiciona complexidade sem benefício — stdin puro já funciona.

**Rationale**: stdin é a abordagem mais simples, sem limite prático de tamanho, já comprovada no runner Gemini e confirmada na issue #1046 do copilot-cli.

### Decisão 2: Manter flags existentes

**Escolha**: Manter `--yolo` e `--silent` na lista de argumentos. Apenas remover `-p` e o prompt da lista.

**Rationale**: Essas flags controlam comportamento do CLI (auto-approve e output limpo), não a forma de input. Devem permanecer como argumentos CLI.

## Risks / Trade-offs

- **[Risco] Versões antigas do copilot CLI podem não suportar stdin** → O suporte a stdin foi confirmado em Jan/2026. Versões anteriores podem falhar silenciosamente (sem ler stdin). Mitigação: documentar versão mínima recomendada.
- **[Risco] Flag `--silent` não é documentada oficialmente** → Pode ter sido renomeada ou removida em versões futuras. Fora do escopo desta change, mas vale monitorar.
- **[Trade-off] Sem fallback para `-p`** → Se stdin falhar por algum motivo, não há fallback automático para argumento CLI. Aceitável porque o cenário de falha é improvável e a causa seria facilmente diagnosticável.
