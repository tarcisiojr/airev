.PHONY: help install install-dev build clean test test-cov lint format check dist publish run release release-dry-run

# Variáveis
PYTHON := python3
PIP := pip
PACKAGE := code_reviewer
SRC_DIR := src
TEST_DIR := tests

# Cores para output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

help: ## Mostra esta ajuda
	@echo "$(BLUE)Code Reviewer - Comandos disponíveis:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================
# Instalação
# ============================================

install: ## Instala o pacote em modo desenvolvimento
	$(PIP) install -e .

install-dev: ## Instala com dependências de desenvolvimento
	$(PIP) install -e ".[dev]"

# ============================================
# Build e Distribuição
# ============================================

build: clean ## Builda o pacote (wheel e sdist)
	$(PYTHON) -m build

dist: build ## Alias para build

clean: ## Remove arquivos de build e cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf $(SRC_DIR)/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

publish-test: build ## Publica no TestPyPI
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish: build ## Publica no PyPI
	$(PYTHON) -m twine upload dist/*

# ============================================
# Release Automation (Semantic Release)
# ============================================

release-dry-run: ## Preview da próxima versão (sem aplicar)
	@echo "$(YELLOW)Analisando commits para determinar próxima versão...$(NC)"
	semantic-release version --print
	@echo ""
	@echo "$(BLUE)Para aplicar o release, execute: make release$(NC)"

release: ## Executa release local (requer credenciais)
	@echo "$(YELLOW)Executando semantic-release...$(NC)"
	semantic-release version
	semantic-release publish
	@echo "$(GREEN)Release concluído!$(NC)"

# ============================================
# Testes e Qualidade
# ============================================

test: ## Executa os testes
	pytest $(TEST_DIR) -v

test-cov: ## Executa testes com cobertura
	pytest $(TEST_DIR) --cov=$(PACKAGE) --cov-report=term-missing --cov-report=html

lint: ## Verifica código com flake8
	flake8 $(SRC_DIR) $(TEST_DIR) --max-line-length=100

format: ## Formata código com black
	black $(SRC_DIR) $(TEST_DIR)

format-check: ## Verifica formatação sem modificar
	black $(SRC_DIR) $(TEST_DIR) --check

check: ## Verifica sintaxe Python
	$(PYTHON) -m py_compile $(SRC_DIR)/$(PACKAGE)/*.py
	$(PYTHON) -m py_compile $(SRC_DIR)/$(PACKAGE)/**/*.py 2>/dev/null || true

typecheck: ## Verifica tipos com mypy
	mypy $(SRC_DIR)/$(PACKAGE)

validate: check lint test ## Executa todas as validações

# ============================================
# Execução
# ============================================

run: ## Executa o CLI (use: make run ARGS="review --base main")
	$(PYTHON) -m $(PACKAGE).cli $(ARGS)

runners: ## Lista runners disponíveis
	airev runners

# ============================================
# Desenvolvimento
# ============================================

dev-setup: install-dev ## Setup completo para desenvolvimento
	@echo "$(GREEN)Ambiente de desenvolvimento configurado!$(NC)"

requirements: ## Gera requirements.txt a partir do pyproject.toml
	$(PIP) freeze > requirements.txt

version: ## Mostra a versão atual
	@$(PYTHON) -c "from $(PACKAGE) import __version__; print(__version__)"
