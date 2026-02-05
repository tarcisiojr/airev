"""Testes para o diff_parser."""

from code_reviewer.diff_parser import (
    get_modified_functions,
    is_ignored_file,
    parse_diff,
)

# Exemplo de diff para testes
SAMPLE_DIFF = """diff --git a/services/payment.py b/services/payment.py
index 1234567..abcdefg 100644
--- a/services/payment.py
+++ b/services/payment.py
@@ -45,7 +45,9 @@ def process_payment(amount, token):
     validated = validate_card(token)
-    result = charge(amount)
+    result = charge(amount, currency="BRL")
+    if not result.success:
+        log_failure(result)
     return result

@@ -82,3 +84,5 @@ def refund_payment(transaction_id):
     transaction = get_transaction(transaction_id)
+    if transaction.is_refundable:
+        return do_refund(transaction)
     return None
diff --git a/routes/checkout.py b/routes/checkout.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/routes/checkout.py
@@ -0,0 +1,15 @@
+from services.payment import process_payment
+
+def checkout_handler(request):
+    amount = request.json["amount"]
+    token = request.json["token"]
+    return process_payment(amount, token)
"""

SAMPLE_DIFF_WITH_LOCK = """diff --git a/package-lock.json b/package-lock.json
index 1234567..abcdefg 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,5 +1,5 @@
 {
-  "version": "1.0.0"
+  "version": "1.0.1"
 }
diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,3 +10,4 @@ def main():
     print("Hello")
+    print("World")
"""


class TestIsIgnoredFile:
    """Testes para função is_ignored_file."""

    def test_ignora_package_lock(self):
        assert is_ignored_file("package-lock.json") is True

    def test_ignora_poetry_lock(self):
        assert is_ignored_file("poetry.lock") is True

    def test_ignora_yarn_lock(self):
        assert is_ignored_file("yarn.lock") is True

    def test_ignora_migrations(self):
        assert is_ignored_file("app/migrations/0001_initial.py") is True

    def test_ignora_pycache(self):
        assert is_ignored_file("src/__pycache__/module.cpython-39.pyc") is True

    def test_nao_ignora_arquivo_normal(self):
        assert is_ignored_file("src/main.py") is False

    def test_nao_ignora_arquivo_js(self):
        assert is_ignored_file("src/app.js") is False

    def test_ignora_minificado(self):
        assert is_ignored_file("dist/bundle.min.js") is True


class TestParseDiff:
    """Testes para função parse_diff."""

    def test_extrai_arquivos_modificados(self):
        files = parse_diff(SAMPLE_DIFF)
        assert len(files) == 2
        assert files[0].path == "services/payment.py"
        assert files[1].path == "routes/checkout.py"

    def test_identifica_arquivo_novo(self):
        files = parse_diff(SAMPLE_DIFF)
        payment_file = files[0]
        checkout_file = files[1]

        assert payment_file.is_new is False
        assert checkout_file.is_new is True

    def test_extrai_hunks(self):
        files = parse_diff(SAMPLE_DIFF)
        payment_file = files[0]

        assert len(payment_file.hunks) == 2

    def test_extrai_nome_funcao_do_hunk(self):
        files = parse_diff(SAMPLE_DIFF)
        payment_file = files[0]

        assert payment_file.hunks[0].function_name == "process_payment"
        assert payment_file.hunks[1].function_name == "refund_payment"

    def test_extrai_linhas_adicionadas(self):
        files = parse_diff(SAMPLE_DIFF)
        payment_file = files[0]
        first_hunk = payment_file.hunks[0]

        assert len(first_hunk.added_lines) == 3
        assert 'result = charge(amount, currency="BRL")' in first_hunk.added_lines[0].content

    def test_extrai_linhas_removidas(self):
        files = parse_diff(SAMPLE_DIFF)
        payment_file = files[0]
        first_hunk = payment_file.hunks[0]

        assert len(first_hunk.removed_lines) == 1
        assert "result = charge(amount)" in first_hunk.removed_lines[0].content

    def test_filtra_arquivos_ignorados(self):
        files = parse_diff(SAMPLE_DIFF_WITH_LOCK)

        # Deve ter apenas o main.py, não o package-lock.json
        assert len(files) == 1
        assert files[0].path == "src/main.py"


class TestGetModifiedFunctions:
    """Testes para função get_modified_functions."""

    def test_retorna_funcoes_modificadas(self):
        files = parse_diff(SAMPLE_DIFF)
        functions = get_modified_functions(files)

        assert len(functions) == 2
        assert ("services/payment.py", "process_payment") in functions
        assert ("services/payment.py", "refund_payment") in functions

    def test_diff_vazio_retorna_lista_vazia(self):
        files = parse_diff("")
        functions = get_modified_functions(files)

        assert functions == []
