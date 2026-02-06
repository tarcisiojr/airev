## 1. Cache Management

- [x] 1.1 Adicionar função `clear_cache()` em `version_check.py` para remover arquivo de cache
- [x] 1.2 Exportar `clear_cache` no `__init__.py` do módulo updater

## 2. Version Detection

- [x] 2.1 Criar função `get_installed_version()` em `upgrade.py` que consulta pipx/pip para obter versão real
- [x] 2.2 Implementar fallback para quando `pipx list --json` não estiver disponível

## 3. Upgrade Logic

- [x] 3.1 Modificar `run_upgrade()` para chamar `clear_cache()` após qualquer tentativa de upgrade
- [x] 3.2 Modificar `run_upgrade()` para verificar versão antes e depois do upgrade
- [x] 3.3 Atualizar mensagens de feedback baseado no resultado real (atualizado vs já atualizado vs falhou)

## 4. Testing

- [x] 4.1 Adicionar testes para `clear_cache()`
- [x] 4.2 Adicionar testes para `get_installed_version()`
- [x] 4.3 Adicionar testes para cenários de upgrade (sucesso, sem mudança, falha)
