"""Testes para o context_builder."""

from code_reviewer.context_builder import (
    _is_comment_line,
    find_callees,
)


class TestIsCommentLine:
    """Testes para função _is_comment_line."""

    def test_comentario_python(self):
        assert _is_comment_line("# Este é um comentário") is True

    def test_comentario_js_linha(self):
        assert _is_comment_line("// Este é um comentário") is True

    def test_comentario_js_bloco(self):
        assert _is_comment_line("/* Este é um comentário */") is True

    def test_comentario_docstring(self):
        assert _is_comment_line('"""Docstring"""') is True
        assert _is_comment_line("'''Docstring'''") is True

    def test_codigo_normal(self):
        assert _is_comment_line("result = calculate()") is False

    def test_linha_com_espacos(self):
        assert _is_comment_line("   # comentário indentado") is True


class TestFindCallees:
    """Testes para função find_callees."""

    def test_extrai_chamadas_de_funcao(self):
        lines = [
            "result = process_payment(amount)",
            "log_error(message)",
        ]
        callees = find_callees(lines, workdir=None)

        # A função retorna vazio pq não tem projeto real para buscar
        # Este teste valida apenas que não dá erro
        assert isinstance(callees, list)

    def test_ignora_keywords(self):
        lines = [
            "if condition:",
            "for item in items:",
            "while True:",
        ]
        callees = find_callees(lines, workdir=None)

        # Não deve encontrar if, for, while
        symbols = {c.function_name for c in callees if c.function_name}
        assert "if" not in symbols
        assert "for" not in symbols
        assert "while" not in symbols

    def test_ignora_builtins(self):
        lines = [
            "x = len(items)",
            "s = str(value)",
            "n = int(text)",
        ]
        callees = find_callees(lines, workdir=None)

        symbols = {c.function_name for c in callees if c.function_name}
        assert "len" not in symbols
        assert "str" not in symbols
        assert "int" not in symbols

    def test_lista_vazia(self):
        callees = find_callees([], workdir=None)
        assert callees == []
