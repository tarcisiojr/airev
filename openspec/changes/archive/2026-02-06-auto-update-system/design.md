## Context

O airev é uma CLI Python distribuída via PyPI. Atualmente não há mecanismo para informar usuários sobre novas versões. CLIs modernas (Claude Code, Copilot CLI, Gemini CLI) implementam verificação de versão no startup com notificação não-intrusiva.

**Estado atual:**
- Versão definida em `__init__.py`
- Nenhum check de versão
- Nenhum comando de upgrade
- Release manual via `make publish`
- Sem automação de versionamento ou changelog

**Constraints:**
- Não adicionar dependências externas para HTTP (usar urllib)
- Check não pode bloquear a execução (timeout curto, falha silenciosa)
- Deve funcionar offline (cache + graceful degradation)

## Goals / Non-Goals

**Goals:**
- Notificar usuários sobre novas versões de forma não-intrusiva
- Fornecer comando simples para upgrade
- Abstrair HTTP client para troca futura
- Respeitar preferências do usuário (opt-out)

**Non-Goals:**
- Auto-update automático (sem intervenção do usuário)
- Download de binários (usa pip/pipx existente)
- Suporte a canais (stable/beta) - apenas latest
- Rollback para versões anteriores

## Decisions

### 1. Estrutura de módulos

```
src/code_reviewer/updater/
├── __init__.py          # Exports: check_for_update(), run_upgrade()
├── http_client.py       # Abstração HTTP (Protocol + UrllibClient)
├── version_check.py     # Lógica de check + cache
└── notifier.py          # Notificação visual (Rich Panel)
```

**Rationale:** Módulo isolado permite evolução independente e facilita testes. Abstração HTTP via Protocol permite trocar implementação sem alterar consumidores.

### 2. Cache de 1 hora em ~/.cache/airev/

**Alternativas consideradas:**
- Sem cache: muitos requests ao PyPI, lento
- Cache em memória: perde entre execuções
- Cache de 24h: usuário pode não ver update por muito tempo

**Decisão:** Cache de 1 hora em arquivo JSON. Balanceia entre responsividade e economia de requests.

```json
{
  "checked_at": "2026-02-06T10:30:00Z",
  "latest_version": "0.2.0"
}
```

### 3. Timeout de 5 segundos com falha silenciosa

**Rationale:**
- 5s é generoso para um GET simples
- Falha silenciosa evita bloquear usuário em redes lentas/offline
- Não impacta a funcionalidade principal

### 4. Detecção de instalador via sys.executable

```python
def detect_installer() -> str:
    if "pipx" in Path(sys.executable).parts:
        return "pipx"
    return "pip"
```

**Rationale:** Simples e funciona para os dois casos principais. Pode ser expandido no futuro.

### 5. Notificação apenas em modo interativo

Suprimir notificação quando:
- `CODE_REVIEWER_NO_UPDATE_CHECK=1`
- `--json-output` está ativo

**Rationale:** Não poluir output estruturado ou ambientes CI.

### 6. Release automation com python-semantic-release

**Alternativas consideradas:**
- bump2version: simples, mas manual (você decide o bump)
- tbump: moderno, mas menos adotado
- python-semantic-release: automático, padrão big techs

**Decisão:** python-semantic-release por seguir o mesmo padrão de CLIs como Copilot CLI e Claude Code.

**Fluxo:**
```
Commit com prefixo → CI analisa → Bump automático → Tag + CHANGELOG → Publish PyPI
```

**Conventional Commits:**
```
feat: nova funcionalidade     → minor bump (0.1.0 → 0.2.0)
fix: correção de bug          → patch bump (0.2.0 → 0.2.1)
feat!: breaking change        → major bump (0.2.1 → 1.0.0)
chore: manutenção             → sem bump
docs: documentação            → sem bump
```

### 7. Single source of truth para versão

**Decisão:** `__init__.py` é a fonte única de versão. pyproject.toml lê dinamicamente.

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "code_reviewer.__version__"}
```

**Rationale:** python-semantic-release atualiza apenas `__init__.py`, evitando dessincronização.

### 8. GitHub Actions para CI/CD

**Workflow release.yml:**
```yaml
on:
  push:
    branches: [main]

jobs:
  release:
    - Checkout
    - Setup Python
    - Install dependencies
    - Run python-semantic-release
    - Publish to PyPI (se nova versão)
```

**Rationale:** Releases automáticos a cada push em main que contenha commits relevantes.

## Risks / Trade-offs

**[PyPI indisponível]** → Falha silenciosa, usa cache se disponível

**[Versão no cache desatualizada]** → TTL de 1h limita impacto

**[Detecção de instalador incorreta]** → Fallback para pip, usuário pode corrigir manualmente

**[Usuário em rede corporativa com proxy]** → urllib respeita variáveis de ambiente HTTP_PROXY/HTTPS_PROXY

**[Cache corrompido]** → Ignorar e fazer novo request

**[Commit sem prefixo convencional]** → Ignorado pelo semantic-release, sem bump

**[PyPI credentials expiradas]** → CI falha, notificação no GitHub Actions

**[Release acidental]** → Só acontece com push em main; usar branch protection
