#!/usr/bin/env python3
"""Suite de avaliação de recall do airev.

Executa o airev contra casos com bugs conhecidos e mede quantos foram
detectados. Use após qualquer mudança no prompt para detectar regressão
de recall.

Cada caso em evals/cases/<nome>/ contém:
- before/: estado inicial do código (branch base)
- after/:  estado com o bug introduzido (branch de feature)
- expected.json: findings esperados (arquivo, categoria, faixa de linhas)

Uso:
    python evals/run_evals.py                    # Todos os casos
    python evals/run_evals.py --case sql_injection
    python evals/run_evals.py --runner copilot --thorough

Requer um runner de IA instalado (gemini ou copilot). Execução manual —
não faz parte da suite pytest por depender de chamadas reais de IA.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASES_DIR = Path(__file__).parent / "cases"

# Ambiente sem telemetria nem verificação de update durante as avaliações
EVAL_ENV = {
    **os.environ,
    "AIREV_NO_TELEMETRY": "1",
    "AIREV_NO_UPDATE_CHECK": "1",
}


def _git(repo: Path, *args: str) -> None:
    """Executa um comando git no repositório de avaliação."""
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=eval@airev.local",
            "-c",
            "user.name=airev-eval",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def preparar_repo(case_dir: Path, repo: Path) -> None:
    """Monta um repositório git com o antes (main) e o depois (feature).

    Args:
        case_dir: Diretório do caso (com before/ e after/)
        repo: Diretório vazio onde o repositório será criado
    """
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
    )

    shutil.copytree(case_dir / "before", repo, dirs_exist_ok=True)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "estado inicial")

    _git(repo, "checkout", "-b", "feature/eval")
    shutil.copytree(case_dir / "after", repo, dirs_exist_ok=True)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "introduz mudança avaliada")


def executar_airev(repo: Path, runner: str, thorough: bool) -> dict:
    """Roda o airev no repositório de avaliação e retorna o JSON.

    Args:
        repo: Repositório preparado
        runner: Runner de IA a usar
        thorough: Se True, usa o modo --thorough

    Returns:
        Resultado do review como dicionário

    Raises:
        RuntimeError: Se a execução ou o parse falharem
    """
    command = [
        sys.executable,
        "-m",
        "code_reviewer.cli",
        "review",
        "--base",
        "main",
        "--runner",
        runner,
        "--json-output",
        "--no-progress",
        "--no-interactive",
        "--min-confidence",
        "1",
    ]
    if thorough:
        command.append("--thorough")

    result = subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=1800,
        env=EVAL_ENV,
    )

    if result.returncode != 0:
        raise RuntimeError(f"airev falhou: {result.stderr.strip()[:500]}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Saída não é JSON válido: {e}") from e


def avaliar_caso(expected: dict, review: dict) -> list[dict]:
    """Compara os findings do review com os esperados.

    Um finding esperado é considerado detectado quando existe um finding
    no mesmo arquivo com linha dentro da faixa. A categoria é comparada
    separadamente (detecção com categoria errada conta como acerto parcial).

    Args:
        expected: Conteúdo do expected.json
        review: Resultado JSON do airev

    Returns:
        Lista de resultados por finding esperado
    """
    findings = review.get("findings", [])
    resultados = []

    for esperado in expected.get("expected_findings", []):
        inicio, fim = esperado["line_range"]
        candidatos = [
            f
            for f in findings
            if f.get("file", "").endswith(esperado["file"])
            and inicio <= f.get("line", 0) <= fim
        ]
        categoria_ok = any(
            f.get("category") == esperado["category"] for f in candidatos
        )

        resultados.append(
            {
                "esperado": esperado,
                "detectado": bool(candidatos),
                "categoria_correta": categoria_ok,
            }
        )

    return resultados


def main() -> int:
    """Executa a suite de avaliação e imprime o resumo de recall."""
    parser = argparse.ArgumentParser(description="Avaliação de recall do airev")
    parser.add_argument("--runner", default="gemini", help="Runner de IA")
    parser.add_argument("--case", default=None, help="Executa apenas um caso")
    parser.add_argument(
        "--thorough", action="store_true", help="Usa o modo --thorough"
    )
    args = parser.parse_args()

    case_dirs = sorted(
        d
        for d in CASES_DIR.iterdir()
        if d.is_dir() and (args.case is None or d.name == args.case)
    )

    if not case_dirs:
        print(f"Nenhum caso encontrado em {CASES_DIR}")
        return 1

    total_esperados = 0
    total_detectados = 0
    total_categoria_correta = 0

    for case_dir in case_dirs:
        expected = json.loads(
            (case_dir / "expected.json").read_text(encoding="utf-8")
        )
        print(f"\n▶ {case_dir.name}: {expected['description']}")

        with tempfile.TemporaryDirectory(prefix="airev-eval-") as tmp:
            repo = Path(tmp)
            try:
                preparar_repo(case_dir, repo)
                review = executar_airev(repo, args.runner, args.thorough)
            except (RuntimeError, subprocess.SubprocessError) as e:
                print(f"  ✗ ERRO: {e}")
                total_esperados += len(expected.get("expected_findings", []))
                continue

        for resultado in avaliar_caso(expected, review):
            total_esperados += 1
            esperado = resultado["esperado"]
            local = f"{esperado['file']}:{esperado['line_range']}"

            if resultado["detectado"] and resultado["categoria_correta"]:
                total_detectados += 1
                total_categoria_correta += 1
                print(f"  ✓ DETECTADO {local} ({esperado['category']})")
            elif resultado["detectado"]:
                total_detectados += 1
                print(f"  ~ DETECTADO com categoria diferente {local}")
            else:
                print(f"  ✗ NÃO DETECTADO {local} ({esperado['category']})")

    if total_esperados == 0:
        print("\nNenhum finding esperado nos casos selecionados.")
        return 1

    recall = total_detectados / total_esperados
    recall_estrito = total_categoria_correta / total_esperados
    print(f"\n{'=' * 50}")
    print(f"Recall (detecção):           {total_detectados}/{total_esperados} = {recall:.0%}")
    print(f"Recall (categoria correta):  {total_categoria_correta}/{total_esperados} = {recall_estrito:.0%}")

    return 0 if recall == 1.0 else 2


if __name__ == "__main__":
    sys.exit(main())
