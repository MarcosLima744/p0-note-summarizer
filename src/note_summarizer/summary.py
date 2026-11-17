from pydantic import BaseModel, ConfigDict, Field

from .config import AppError
from .notes import Note


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(StrictModel):
    arquivo: str = Field(min_length=1)
    trecho: str = Field(min_length=1)


class Topic(StrictModel):
    assunto: str = Field(min_length=1)
    sintese: str = Field(min_length=1)
    dificuldades: list[str]


class Task(StrictModel):
    descricao: str = Field(min_length=1)
    conferir: bool
    referencias: list[Evidence] = Field(min_length=1)


class Summary(StrictModel):
    assuntos: list[Topic] = Field(min_length=1)
    tarefas: list[Task]


def validate_evidence(summary: Summary, notes: list[Note]) -> None:
    sources = {note.filename: note.text for note in notes}
    for topic in summary.assuntos:
        if not topic.assunto.strip() or not topic.sintese.strip():
            raise AppError("O modelo retornou um resumo vazio ou inválido.")
    for task in summary.tarefas:
        if not task.descricao.strip():
            raise AppError("O modelo retornou uma tarefa vazia.")
        for ref in task.referencias:
            if (ref.arquivo not in sources or not ref.trecho.strip()
                    or ref.trecho not in sources[ref.arquivo]):
                raise AppError("O modelo citou uma referência inexistente. A síntese não foi salva; tente novamente.")


def render_markdown(summary: Summary) -> str:
    lines = ["# Síntese semanal de estudos", "", "## Resumo da semana", ""]
    for topic in summary.assuntos:
        lines.extend([f"### {topic.assunto}", "", topic.sintese, ""])
        if topic.dificuldades:
            lines.append("Dificuldades registradas:")
            lines.extend(f"- {item}" for item in topic.dificuldades)
            lines.append("")
    lines.extend(["## Tarefas identificadas", ""])
    if not summary.tarefas:
        lines.append("Nenhuma tarefa identificada.")
    for task in summary.tarefas:
        flag = " **[Conferir: situação ambígua]**" if task.conferir else ""
        lines.append(f"- [ ] {task.descricao}{flag}")
        for ref in task.referencias:
            quote = " ".join(ref.trecho.split())
            lines.append(f"  - Origem: `{ref.arquivo}` — “{quote}”")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
