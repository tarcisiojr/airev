"""Description Input - Captura de descrição das alterações."""

import select
import sys

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.key_binding import KeyBindings

# Limite máximo de caracteres para a descrição
MAX_DESCRIPTION_LENGTH = 2000


def read_from_stdin() -> str | None:
    """Lê descrição de stdin (para uso com pipe ou redirecionamento).

    Returns:
        Conteúdo de stdin ou None se stdin estiver vazio
    """
    # Verifica se há dados disponíveis em stdin sem bloquear
    if not sys.stdin.isatty():
        # Stdin não é TTY, pode ter dados via pipe
        if select.select([sys.stdin], [], [], 0.0)[0]:
            content = sys.stdin.read()
            return content.strip() if content.strip() else None
    return None


def is_interactive_mode(no_interactive: bool, json_output: bool) -> bool:
    """Verifica se deve usar modo interativo.

    Args:
        no_interactive: Flag --no-interactive foi passada
        json_output: Flag --json-output foi passada

    Returns:
        True se deve perguntar interativamente
    """
    if no_interactive:
        return False
    if json_output:
        return False
    if not sys.stdout.isatty():
        return False
    if not sys.stdin.isatty():
        return False
    return True


def ask_description_interactive() -> str | None:
    """Pergunta descrição ao usuário de forma interativa.

    Usa prompt_toolkit para suportar input multi-linha com bracketed paste.

    Returns:
        Descrição digitada/colada ou None se usuário pulou
    """
    # Configura key bindings para finalizar com Enter em linha vazia
    bindings = KeyBindings()

    print("📝 Descrição das alterações:")
    print("   (Cole ou digite. Enter em linha vazia para enviar, Ctrl+C para pular)\n")

    try:
        text = pt_prompt(
            "> ",
            multiline=True,
            key_bindings=bindings,
        )
        return text.strip() if text.strip() else None
    except KeyboardInterrupt:
        # Ctrl+C: continuar sem descrição
        print()  # Nova linha após ^C
        return None
    except EOFError:
        # Ctrl+D: finalizar input
        return None


def truncate_description(description: str, reporter=None) -> str:
    """Trunca descrição se exceder o limite.

    Args:
        description: Descrição original
        reporter: ProgressReporter opcional para exibir aviso

    Returns:
        Descrição truncada se necessário
    """
    if len(description) <= MAX_DESCRIPTION_LENGTH:
        return description

    truncated = description[:MAX_DESCRIPTION_LENGTH]

    if reporter:
        reporter.warning(
            f"Descrição truncada de {len(description)} para {MAX_DESCRIPTION_LENGTH} caracteres"
        )

    return truncated


def get_description(
    description_flag: str | None,
    no_interactive: bool,
    json_output: bool,
    reporter=None,
) -> str | None:
    """Obtém a descrição das alterações.

    Ordem de prioridade:
    1. Flag --description com valor direto
    2. Flag --description com "-" (ler de stdin)
    3. Prompt interativo (se modo interativo ativo)

    Args:
        description_flag: Valor da flag --description ou None
        no_interactive: Flag --no-interactive foi passada
        json_output: Flag --json-output foi passada
        reporter: ProgressReporter opcional para exibir mensagens

    Returns:
        Descrição das alterações ou None se não fornecida
    """
    description = None

    # Caso 1: Flag com valor direto
    if description_flag and description_flag != "-":
        description = description_flag

    # Caso 2: Flag com "-" (ler de stdin)
    elif description_flag == "-":
        description = read_from_stdin()

    # Caso 3: Modo interativo
    elif is_interactive_mode(no_interactive, json_output):
        description = ask_description_interactive()

    # Aplica truncamento se necessário
    if description:
        description = truncate_description(description, reporter)

    return description
