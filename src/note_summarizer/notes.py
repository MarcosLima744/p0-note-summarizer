from dataclasses import dataclass
from pathlib import Path

from .config import AppError


@dataclass(frozen=True)
class Note:
    filename: str
    text: str


def read_notes(directory: Path, max_chars: int) -> list[Note]:
    if not directory.is_dir():
        raise AppError("A entrada deve ser um diretório existente com arquivos .txt.")
    notes = []
    total = 0
    try:
        for path in sorted(directory.iterdir()):
            if path.suffix.lower() != ".txt":
                continue
            if path.is_symlink():
                raise AppError("A pasta contém um .txt que é link simbólico; use arquivos locais.")
            if not path.is_file():
                continue
            # Leitura limitada também impede carregar um arquivo enorme em memória.
            with path.open("rb") as stream:
                raw = stream.read(max_chars * 4 + 1)
            if len(raw) > max_chars * 4:
                raise AppError("As anotações excedem NOTES_MAX_INPUT_CHARS; reduza a entrada.")
            text = raw.decode("utf-8-sig")
            total += len(text)
            if total > max_chars:
                raise AppError("As anotações excedem NOTES_MAX_INPUT_CHARS; reduza a entrada.")
            if text.strip():
                notes.append(Note(path.name, text))
    except UnicodeError:
        raise AppError("Não foi possível ler um .txt como UTF-8. Converta a codificação.") from None
    except OSError:
        raise AppError("Não foi possível ler a pasta ou um dos arquivos .txt. Verifique as permissões.") from None
    if not notes:
        raise AppError("A pasta não contém arquivos .txt com conteúdo útil.")
    return notes


def validate_output(directory: Path, output: Path) -> None:
    if output.resolve().is_relative_to(directory.resolve()):
        raise AppError("Escolha um arquivo de saída fora da pasta de entrada.")
    if output.exists() or output.is_symlink():
        raise AppError("O arquivo de saída já existe. Escolha outro nome com --output.")
