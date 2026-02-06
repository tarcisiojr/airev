## Context

O módulo `i18n` carrega arquivos de tradução de `LOCALES_DIR = Path(__file__).parent.parent / "locales"`. Isso funciona em desenvolvimento porque os arquivos estão presentes no diretório fonte. Porém, quando o pacote é instalado via pip/pipx, apenas os arquivos explicitamente listados em `package-data` são incluídos.

Configuração atual em `pyproject.toml`:
```toml
[tool.setuptools.package-data]
code_reviewer = ["prompts/*.md"]
```

Os arquivos `locales/*.yaml` não estão listados, então não são empacotados.

## Goals / Non-Goals

**Goals:**
- Incluir os arquivos `locales/*.yaml` no bundle de distribuição
- Manter compatibilidade com a lógica atual do módulo i18n (sem alterações de código)

**Non-Goals:**
- Alterar a forma como o i18n carrega os arquivos
- Adicionar novos idiomas ou traduções
- Modificar a estrutura de diretórios

## Decisions

**Decisão 1: Adicionar `locales/*.yaml` ao package-data**

Alterar a configuração de:
```toml
code_reviewer = ["prompts/*.md"]
```

Para:
```toml
code_reviewer = ["prompts/*.md", "locales/*.yaml"]
```

*Alternativa considerada*: Usar `include_package_data = true` com MANIFEST.in - rejeitada por ser mais complexa para um caso simples.

## Risks / Trade-offs

- **[Risco baixo]** Aumento mínimo no tamanho do pacote (~2KB por arquivo YAML) → Aceitável, são arquivos pequenos de texto.
- **[Risco baixo]** Se novos arquivos de locale forem adicionados com extensão diferente de `.yaml`, não serão incluídos → Mitigação: manter convenção de usar `.yaml` para todos os locales.
