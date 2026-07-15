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

    def test_formata_linhas_contexto_com_espaco(self):
        """Verifica que linhas de contexto são formatadas com espaço inicial."""
        diff_file = DiffFile(
            path="test.py",
            hunks=[
                DiffHunk(
                    function_name="my_func",
                    start_line_old=10,
                    start_line_new=10,
                    added_lines=[
                        DiffLine(line_number=12, content="    linha_nova()", is_addition=True)
                    ],
                    removed_lines=[],
                    context_lines=[
                        DiffLine(line_number=11, content="    if (", is_addition=False),
                        DiffLine(line_number=13, content="    ):", is_addition=False),
                    ],
                )
            ],
        )

        result = format_diff_for_prompt([diff_file])

        # Linhas de contexto devem ter espaço como prefixo
        assert "     if (" in result  # espaço do diff + indentação original
        assert "     ):" in result
        # Linha adicionada deve ter +
        assert "+    linha_nova()" in result

    def test_ordena_linhas_por_numero(self):
        """Verifica que linhas são ordenadas pelo número de linha."""
        diff_file = DiffFile(
            path="test.py",
            hunks=[
                DiffHunk(
                    function_name="my_func",
                    start_line_old=10,
                    start_line_new=10,
                    added_lines=[
                        DiffLine(line_number=12, content="linha_b()", is_addition=True)
                    ],
                    removed_lines=[
                        DiffLine(line_number=11, content="linha_removida()", is_addition=False)
                    ],
                    context_lines=[
                        DiffLine(line_number=10, content="if True:", is_addition=False),
                        DiffLine(line_number=13, content="return", is_addition=False),
                    ],
                )
            ],
        )

        result = format_diff_for_prompt([diff_file])
        lines = result.split("\n")

        # Procura os índices das linhas relevantes
        idx_if = next(i for i, l in enumerate(lines) if "if True" in l)
        idx_removed = next(i for i, l in enumerate(lines) if "linha_removida" in l)
        idx_added = next(i for i, l in enumerate(lines) if "linha_b" in l)
        idx_return = next(i for i, l in enumerate(lines) if "return" in l)

        # Verifica ordem: if < removida < adicionada < return
        assert idx_if < idx_removed < idx_added < idx_return

    def test_preserva_indentacao_contexto(self):
        """Verifica que a indentação original das linhas de contexto é preservada."""
        diff_file = DiffFile(
            path="test.py",
            hunks=[
                DiffHunk(
                    function_name="nested",
                    start_line_old=20,
                    start_line_new=20,
                    added_lines=[
                        DiffLine(line_number=22, content="            deep_call()", is_addition=True)
                    ],
                    removed_lines=[],
                    context_lines=[
                        DiffLine(line_number=21, content="        for x in items:", is_addition=False),
                    ],
                )
            ],
        )

        result = format_diff_for_prompt([diff_file])

        # Deve preservar a indentação (8 espaços + espaço do diff)
        assert "         for x in items:" in result
        # Adição com 12 espaços
        assert "+            deep_call()" in result


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

    def test_janela_centrada_no_hunk_em_arquivo_grande(self):
        # Arquivo com 500 linhas e hunk modificado na linha 400 —
        # o truncamento antigo (primeiras 200 linhas) esconderia a região
        big_content = "\n".join([f"linha {i}" for i in range(1, 501)])

        graph = ContextGraph(
            function_name="funcao_final",
            file="big.py",
            callers=[],
            callees=[],
            file_content=big_content,
        )

        diff_file = DiffFile(
            path="big.py",
            hunks=[
                DiffHunk(
                    start_line_old=400,
                    start_line_new=400,
                    added_lines=[
                        DiffLine(
                            line_number=400, content="linha 400", is_addition=True
                        )
                    ],
                )
            ],
        )

        result = format_context_for_prompt([graph], [diff_file])

        # A região do hunk (linha 400 ± janela) deve estar presente
        assert "linha 400" in result
        assert "linha 380" in result
        # O cabeçalho do arquivo (imports/globals) também
        assert "linha 1\n" in result
        # O meio do arquivo, distante do hunk, deve ser omitido
        assert "linha 200\n" not in result
        assert "omitidas" in result

    def test_arquivo_pequeno_vai_inteiro_mesmo_com_hunks(self):
        content = "\n".join([f"linha {i}" for i in range(1, 51)])

        graph = ContextGraph(
            function_name="f",
            file="small.py",
            callers=[],
            callees=[],
            file_content=content,
        )

        diff_file = DiffFile(
            path="small.py",
            hunks=[
                DiffHunk(
                    start_line_old=10,
                    start_line_new=10,
                    added_lines=[
                        DiffLine(line_number=10, content="linha 10", is_addition=True)
                    ],
                )
            ],
        )

        result = format_context_for_prompt([graph], [diff_file])

        assert "linha 1\n" in result
        assert "linha 50" in result
        assert "omitidas" not in result


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


class TestGetFocusSection:
    """Testes para a seção de foco do modo --thorough."""

    def test_sem_foco_retorna_vazio(self):
        from code_reviewer.prompt_builder import get_focus_section

        assert get_focus_section(None) == ""

    def test_com_foco_inclui_instrucao(self):
        from code_reviewer.prompt_builder import get_focus_section

        section = get_focus_section("Segurança: injeção e secrets")

        assert "FOCO DESTA PASSADA" in section
        assert "Segurança: injeção e secrets" in section

    def test_build_prompt_substitui_placeholder_de_foco(self):
        from code_reviewer.prompt_builder import build_prompt

        prompt = build_prompt([], [], "feature/x", "main", focus="Performance")

        assert "{focus_section}" not in prompt
        assert "Performance" in prompt

    def test_build_prompt_sem_foco_remove_placeholder(self):
        from code_reviewer.prompt_builder import build_prompt

        prompt = build_prompt([], [], "feature/x", "main")

        assert "{focus_section}" not in prompt
        assert "FOCO DESTA PASSADA" not in prompt


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
