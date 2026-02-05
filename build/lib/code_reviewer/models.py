"""Modelos Pydantic para o Code Reviewer."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severidade de um finding."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class Category(str, Enum):
    """Categoria de um finding."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    BUG = "bug"
    RESOURCE_LEAK = "resource-leak"


class DiffLine(BaseModel):
    """Uma linha do diff."""

    line_number: int = Field(description="Número da linha no arquivo")
    content: str = Field(description="Conteúdo da linha")
    is_addition: bool = Field(description="True se linha adicionada (+)")


class DiffHunk(BaseModel):
    """Um hunk do diff (bloco de mudanças)."""

    function_name: Optional[str] = Field(
        default=None, description="Nome da função extraído do hunk header"
    )
    start_line_old: int = Field(description="Linha inicial no arquivo antigo")
    start_line_new: int = Field(description="Linha inicial no arquivo novo")
    added_lines: list[DiffLine] = Field(
        default_factory=list, description="Linhas adicionadas"
    )
    removed_lines: list[DiffLine] = Field(
        default_factory=list, description="Linhas removidas"
    )


class DiffFile(BaseModel):
    """Um arquivo modificado no diff."""

    path: str = Field(description="Caminho do arquivo relativo à raiz do repositório")
    hunks: list[DiffHunk] = Field(default_factory=list, description="Hunks do arquivo")
    is_new: bool = Field(default=False, description="True se arquivo foi criado")
    is_deleted: bool = Field(default=False, description="True se arquivo foi removido")


class FunctionRef(BaseModel):
    """Referência a uma função (caller ou callee)."""

    file: str = Field(description="Caminho do arquivo")
    line: int = Field(description="Número da linha")
    snippet: str = Field(description="Trecho de código ao redor")
    function_name: Optional[str] = Field(
        default=None, description="Nome da função, se identificado"
    )


class ContextGraph(BaseModel):
    """Grafo de contexto para uma função modificada."""

    function_name: str = Field(description="Nome da função modificada")
    file: str = Field(description="Arquivo onde a função está")
    callers: list[FunctionRef] = Field(
        default_factory=list, description="Funções que chamam esta"
    )
    callees: list[FunctionRef] = Field(
        default_factory=list, description="Funções chamadas por esta"
    )
    file_content: Optional[str] = Field(
        default=None, description="Conteúdo completo do arquivo"
    )


class Finding(BaseModel):
    """Um achado da análise de código."""

    file: str = Field(description="Caminho do arquivo")
    line: int = Field(description="Número da linha")
    severity: Severity = Field(description="Severidade: CRITICAL, WARNING, INFO")
    category: Category = Field(
        description="Categoria: security, performance, bug, resource-leak"
    )
    title: str = Field(description="Título curto do problema")
    description: str = Field(description="Descrição detalhada do problema")
    suggestion: str = Field(default="", description="Sugestão de correção")
    code_snippet: str = Field(default="", description="Trecho de código relevante")


class ReviewSummary(BaseModel):
    """Resumo da análise."""

    total: int = Field(description="Total de findings")
    critical: int = Field(default=0, description="Quantidade de CRITICAL")
    warning: int = Field(default=0, description="Quantidade de WARNING")
    info: int = Field(default=0, description="Quantidade de INFO")


class ReviewResult(BaseModel):
    """Resultado completo da análise."""

    branch: str = Field(description="Branch analisada")
    base: str = Field(description="Branch base de comparação")
    files_analyzed: int = Field(description="Quantidade de arquivos analisados")
    findings: list[Finding] = Field(
        default_factory=list, description="Lista de findings"
    )
    summary: ReviewSummary = Field(description="Resumo da análise")
    raw_response: Optional[str] = Field(
        default=None, description="Resposta raw da IA se parsing falhou"
    )
