# Contribuindo para o airev

Obrigado pelo interesse em contribuir! Este documento explica como contribuir para o projeto.

## Configuração do Ambiente

```bash
# Clone o repositório
git clone https://github.com/tarcisiojr/airev.git
cd airev

# Crie um virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale as dependências de desenvolvimento
pip install -e ".[dev]"
```

## Conventional Commits

Este projeto usa [Conventional Commits](https://www.conventionalcommits.org/) para mensagens de commit. Isso permite gerar changelogs automaticamente e determinar versões semanticamente.

### Formato

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de Commit

| Tipo | Descrição | Versão |
|------|-----------|--------|
| `feat` | Nova funcionalidade | Minor (0.x.0) |
| `fix` | Correção de bug | Patch (0.0.x) |
| `docs` | Documentação apenas | - |
| `style` | Formatação, ponto-e-vírgula, etc. | - |
| `refactor` | Refatoração sem mudança de funcionalidade | - |
| `perf` | Melhoria de performance | Patch |
| `test` | Adição ou correção de testes | - |
| `build` | Mudanças no build ou dependências | - |
| `ci` | Mudanças em CI/CD | - |
| `chore` | Manutenção geral | - |

### Breaking Changes

Para indicar uma breaking change (major version), adicione `!` após o tipo ou use o rodapé `BREAKING CHANGE:`:

```bash
# Usando !
feat!: remove suporte a Python 3.9

# Usando rodapé
feat: muda formato de saída JSON

BREAKING CHANGE: O campo 'findings' agora é um array ao invés de objeto
```

### Exemplos

```bash
# Nova funcionalidade
feat: add suporte a runner Claude

# Correção de bug
fix: corrige parsing de diff com caracteres especiais

# Com escopo
feat(cli): add opção --verbose

# Documentação
docs: atualiza README com exemplos de uso

# Refatoração
refactor(parser): simplifica lógica de detecção de funções

# Breaking change
feat!: muda interface do AIRunner
```

## Fluxo de Desenvolvimento

1. **Crie uma branch** a partir de `main`:
   ```bash
   git checkout -b feat/minha-feature
   ```

2. **Faça seus commits** seguindo Conventional Commits

3. **Execute os testes**:
   ```bash
   make test
   ```

4. **Verifique o código**:
   ```bash
   make validate
   ```

5. **Crie um Pull Request** para `main`

## Comandos Úteis

```bash
make help           # Lista todos os comandos disponíveis
make test           # Executa testes
make test-cov       # Testes com cobertura
make lint           # Verifica código com flake8
make format         # Formata código com black
make validate       # Executa todas as validações
make release-dry-run # Preview da próxima versão
```

## Release

Releases são automáticos via GitHub Actions. Quando um PR é mergeado em `main`:

1. O semantic-release analisa os commits
2. Determina a próxima versão baseado nos prefixos
3. Atualiza o CHANGELOG.md
4. Cria uma tag Git
5. Publica no PyPI

## Dúvidas?

Abra uma issue no GitHub ou entre em contato com os mantenedores.
