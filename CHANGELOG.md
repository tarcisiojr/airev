# CHANGELOG

<!-- version list -->

## v1.11.1 (2026-07-15)

### Bug Fixes

- Corrige pacote npm do Gemini CLI na documentação
  ([`7c02603`](https://github.com/tarcisiojr/airev/commit/7c0260312bc98dc4e58981b04c31a50ccf87517f))


## v1.11.0 (2026-07-15)

### Bug Fixes

- Falha do runner de IA não vira mais review vazio silencioso
  ([`8eb6691`](https://github.com/tarcisiojr/airev/commit/8eb66915e18067a6571b2c03771749ce9f4f40fa))

### Features

- Análise estática multi-linguagem, contexto janelado e modo --thorough
  ([`5c6f1d7`](https://github.com/tarcisiojr/airev/commit/5c6f1d7d48c13d6f8ed5ade1d82594bb6741d201))

- Runner para Claude Code CLI
  ([`8373fab`](https://github.com/tarcisiojr/airev/commit/8373fabe39b2df8c0fe00d389d73554b61f25607))

### Testing

- Suite de avaliação de recall com bugs conhecidos
  ([`f4b2aff`](https://github.com/tarcisiojr/airev/commit/f4b2afffe96eef8d7d6e99995506aacc09692f7c))


## v1.10.3 (2026-03-04)

### Bug Fixes

- Suprimindo erros de telemetria
  ([`1d223c3`](https://github.com/tarcisiojr/airev/commit/1d223c3956b191bf260482fcfb9e21f3fcf4199e))


## v1.10.2 (2026-03-04)

### Bug Fixes

- Suprimindo erros.
  ([`68f62d6`](https://github.com/tarcisiojr/airev/commit/68f62d66c886edb223d454728769403ea06ebd24))


## v1.10.1 (2026-03-04)

### Bug Fixes

- Coleta de analytics
  ([`12372b3`](https://github.com/tarcisiojr/airev/commit/12372b301262f1cd95449ec1604b1efc0b522c15))


## v1.10.0 (2026-03-04)

### Features

- Implementação de telemetria com PostHog
  ([`7ba236d`](https://github.com/tarcisiojr/airev/commit/7ba236dd0d1d8cfee8a23a22e720544243885a31))


## v1.9.0 (2026-03-03)

### Features

- Refatorar prompt interativo de descrição para melhorar usabilidade e intuitividade
  ([`3e4583e`](https://github.com/tarcisiojr/airev/commit/3e4583e1f4b9487176773bd028c16d93c3b90a55))

- Remover implementação antiga do CopilotCLIRunner e adicionar nova abordagem para passar prompt via
  stdin
  ([`0b66a04`](https://github.com/tarcisiojr/airev/commit/0b66a044e440f0a2d2988ef0b8f0c83a818640ad))


## v1.8.0 (2026-02-27)

### Features

- Update CopilotCLIRunner to pass prompt via stdin to avoid ARG_MAX limit
  ([`2950870`](https://github.com/tarcisiojr/airev/commit/2950870ff473c34a797c1fa44542d24a59960c82))


## v1.7.0 (2026-02-13)

### Features

- Add --show-deps flag to visualize function dependency graphs in CLI
  ([`c26dc7a`](https://github.com/tarcisiojr/airev/commit/c26dc7a7507ff14ab0962e76c2a3425da0d5d7e5))


## v1.6.0 (2026-02-11)

### Features

- Enhance review quality and context understanding
  ([`9c025a2`](https://github.com/tarcisiojr/airev/commit/9c025a2b0fb8330dd871abdddb38a6583e5c1482))


## v1.5.0 (2026-02-10)

### Chores

- Enhance review quality with structured prompts
  ([`648e352`](https://github.com/tarcisiojr/airev/commit/648e352fde82b30e67387dd4e0c2439cfcee3f6d))

### Documentation

- Update specifications and tasks for new features
  ([`648e352`](https://github.com/tarcisiojr/airev/commit/648e352fde82b30e67387dd4e0c2439cfcee3f6d))

### Features

- Add PR description input via CLI and stdin
  ([`648e352`](https://github.com/tarcisiojr/airev/commit/648e352fde82b30e67387dd4e0c2439cfcee3f6d))


## v1.4.0 (2026-02-10)

### Features

- Add description input feature to CLI for enhanced code review context
  ([`473daf3`](https://github.com/tarcisiojr/airev/commit/473daf317a3e9f2289ee232d31f0538dd38125ac))


## v1.3.0 (2026-02-06)

### Features

- Funcionalidade pra revisao ortografica
  ([`74ef101`](https://github.com/tarcisiojr/airev/commit/74ef10133a341ad666b5e67ecc62fb132e24adcc))


## v1.2.0 (2026-02-06)

### Features

- Implement cache invalidation and version verification after upgrade
  ([`80ad7b2`](https://github.com/tarcisiojr/airev/commit/80ad7b25a970af8769775bd93ce8454f6e4cd299))

### Refactoring

- Rename code-reviewer references to airev
  ([`6bc0bc7`](https://github.com/tarcisiojr/airev/commit/6bc0bc7710e834dbdb2152b5762a3e453e79d49e))


## v1.1.1 (2026-02-06)

### Bug Fixes

- Include locale files in package distribution
  ([`e365111`](https://github.com/tarcisiojr/airev/commit/e365111ddcef5e750e09e87ae88bf590b5dd3338))


## v1.1.0 (2026-02-06)

### Features

- Rebatizando app
  ([`4c8c672`](https://github.com/tarcisiojr/airev/commit/4c8c672ef6c440866ee27734c676ff9a3a97f6c9))


## v1.0.0 (2026-02-06)

- Initial Release
