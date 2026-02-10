"""Testes para o prompt_builder."""

from code_reviewer.models import ContextGraph, DiffFile, DiffHunk, DiffLine, FunctionRef
from code_reviewer.prompt_builder import (
    build_prompt,
    format_context_for_prompt,
    format_diff_for_prompt,
    format_references_for_prompt,
    get_description_section,
    get_prompt_template,
)


class TestGetPromptTemplate:
    """Testes para função get_prompt_template."""

    def test_carrega_template(self):
        template = get_prompt_template()

        assert isinstance(template, str)
        assert len(template) > 100
        assert "{diff}" in template
        assert "{context}" in template
        assert "{references}" in template
        assert "{json_schema}" in template


class TestFormatDiffForPrompt:
    """Testes para função format_diff_for_prompt."""

    def test_formata_arquivo_com_hunks(self):
        diff_file = DiffFile(
            path="services/payment.py",
            hunks=[
                DiffHunk(
                    function_name="process_payment",
                    start_line_old=45,
                    start_line_new=45,
                    added_lines=[
                        DiffLine(line_number=46, content="    nova_linha()", is_addition=True)
                    ],
                    removed_lines=[
                        DiffLine(line_number=46, content="    linha_antiga()", is_addition=False)
                    ],
                )
            ],
        )

        result = format_diff_for_prompt([diff_file])

        assert "services/payment.py" in result
        assert "process_payment" in result
        assert "+    nova_linha()" in result
        assert "-    linha_antiga()" in result

    def test_arquivo_novo(self):
        diff_file = DiffFile(path="novo.py", is_new=True, hunks=[])

        result = format_diff_for_prompt([diff_file])

        assert "novo.py" in result
        assert "(arquivo novo)" in result

    def test_arquivo_deletado(self):
        diff_file = DiffFile(path="removido.py", is_deleted=True, hunks=[])

        result = format_diff_for_prompt([diff_file])

        assert "removido.py" in result
        assert "(arquivo removido)" in result


class TestFormatContextForPrompt:
    """Testes para função format_context_for_prompt."""

    def test_formata_contexto_com_conteudo(self):
        graph = ContextGraph(
            function_name="test_func",
            file="test.py",
            callers=[],
            callees=[],
            file_content="def test_func():\n    pass\n",
        )

        result = format_context_for_prompt([graph])

        assert "test.py" in result
        assert "def test_func():" in result

    def test_limita_conteudo_grande(self):
        # Conteúdo com mais de 200 linhas
        big_content = "\n".join([f"linha {i}" for i in range(300)])

        graph = ContextGraph(
            function_name="big_func",
            file="big.py",
            callers=[],
            callees=[],
            file_content=big_content,
        )

        result = format_context_for_prompt([graph])

        assert "linhas omitidas" in result


class TestFormatReferencesForPrompt:
    """Testes para função format_references_for_prompt."""

    def test_formata_callers(self):
        graph = ContextGraph(
            function_name="process_payment",
            file="payment.py",
            callers=[
                FunctionRef(file="checkout.py", line=32, snippet="process_payment(amount)")
            ],
            callees=[],
        )

        result = format_references_for_prompt([graph])

        assert "process_payment" in result
        assert "Chamada por:" in result
        assert "checkout.py:32" in result

    def test_formata_callees(self):
        graph = ContextGraph(
            function_name="process_payment",
            file="payment.py",
            callers=[],
            callees=[
                FunctionRef(
                    file="utils.py", line=10, snippet="def log_error", function_name="log_error"
                )
            ],
        )

        result = format_references_for_prompt([graph])

        assert "Usa:" in result
        assert "log_error" in result
        assert "utils.py:10" in result

    def test_sem_referencias(self):
        graph = ContextGraph(
            function_name="isolated",
            file="isolated.py",
            callers=[],
            callees=[],
        )

        result = format_references_for_prompt([graph])

        assert "sem referências encontradas" in result


class TestBuildPrompt:
    """Testes para função build_prompt."""

    def test_monta_prompt_completo(self):
        diff_files = [
            DiffFile(
                path="test.py",
                hunks=[
                    DiffHunk(
                        function_name="test",
                        start_line_old=1,
                        start_line_new=1,
                        added_lines=[DiffLine(line_number=2, content="print('hi')", is_addition=True)],
                        removed_lines=[],
                    )
                ],
            )
        ]

        context_graphs = [
            ContextGraph(
                function_name="test",
                file="test.py",
                callers=[],
                callees=[],
                file_content="def test():\n    print('hi')\n",
            )
        ]

        prompt = build_prompt(diff_files, context_graphs, "feature/test", "main")

        # Verifica que o template foi carregado e preenchido
        assert "REGRAS" in prompt
        assert "test.py" in prompt
        assert "review" in prompt  # Schema JSON

    def test_prompt_sem_text_quality_por_padrao(self):
        """Verifica que seção text-quality não aparece quando flag desativada."""
        diff_files = [
            DiffFile(
                path="test.py",
                hunks=[
                    DiffHunk(
                        function_name="test",
                        start_line_old=1,
                        start_line_new=1,
                        added_lines=[],
                        removed_lines=[],
                    )
                ],
            )
        ]
        context_graphs = []

        prompt = build_prompt(diff_files, context_graphs, "feature/test", "main")

        # Não deve conter seção de text-quality
        assert "QUALIDADE DE TEXTO" not in prompt
        assert "text-quality" not in prompt

    def test_prompt_com_text_quality_ativo(self):
        """Verifica que seção text-quality aparece quando flag ativada."""
        diff_files = [
            DiffFile(
                path="test.py",
                hunks=[
                    DiffHunk(
                        function_name="test",
                        start_line_old=1,
                        start_line_new=1,
                        added_lines=[],
                        removed_lines=[],
                    )
                ],
            )
        ]
        context_graphs = []

        prompt = build_prompt(
            diff_files, context_graphs, "feature/test", "main", text_quality=True
        )

        # Deve conter seção de text-quality
        assert "QUALIDADE DE TEXTO" in prompt
        assert "text-quality" in prompt
        assert "ortografia" in prompt
        assert "raise *Error" in prompt
        assert "locales/" in prompt

    def test_prompt_text_quality_menciona_ignorar_identificadores(self):
        """Verifica que instruções de exclusão estão presentes."""
        diff_files = []
        context_graphs = []

        prompt = build_prompt(
            diff_files, context_graphs, "feature/test", "main", text_quality=True
        )

        # Deve instruir a ignorar identificadores
        assert "snake_case" in prompt
        assert "camelCase" in prompt
        assert "termos técnicos" in prompt or "Termos técnicos" in prompt

    def test_prompt_sem_descricao_por_padrao(self):
        """Verifica que seção de descrição não aparece por padrão."""
        diff_files = []
        context_graphs = []

        prompt = build_prompt(diff_files, context_graphs, "feature/test", "main")

        assert "DESCRIÇÃO DAS ALTERAÇÕES" not in prompt

    def test_prompt_com_descricao(self):
        """Verifica que seção de descrição aparece quando fornecida."""
        diff_files = []
        context_graphs = []

        prompt = build_prompt(
            diff_files,
            context_graphs,
            "feature/test",
            "main",
            description="Implementa autenticação MFA",
        )

        assert "DESCRIÇÃO DAS ALTERAÇÕES" in prompt
        assert "Implementa autenticação MFA" in prompt

    def test_prompt_descricao_multilinhas(self):
        """Verifica que descrição multi-linha é preservada."""
        diff_files = []
        context_graphs = []
        description = """## O que muda

- Adiciona MFA
- Corrige bug de login

## Como testar

1. Faça login
2. Verifique MFA"""

        prompt = build_prompt(
            diff_files,
            context_graphs,
            "feature/test",
            "main",
            description=description,
        )

        assert "## O que muda" in prompt
        assert "- Adiciona MFA" in prompt
        assert "## Como testar" in prompt


class TestGetDescriptionSection:
    """Testes para função get_description_section."""

    def test_descricao_none_retorna_vazio(self):
        """Verifica que descrição None retorna string vazia."""
        result = get_description_section(None)
        assert result == ""

    def test_descricao_vazia_retorna_vazio(self):
        """Verifica que descrição vazia retorna string vazia."""
        result = get_description_section("")
        assert result == ""

    def test_descricao_formata_secao(self):
        """Verifica que descrição é formatada corretamente."""
        result = get_description_section("Corrige bug de login")

        assert "DESCRIÇÃO DAS ALTERAÇÕES" in result
        assert "Corrige bug de login" in result
        assert "desenvolvedor" in result.lower()
