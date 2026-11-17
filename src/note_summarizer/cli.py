import argparse
import logging
import sys
from pathlib import Path

from .config import AppError, Config
from .llm import summarize
from .notes import read_notes, validate_output
from .summary import render_markdown

logger = logging.getLogger("note_summarizer")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sintetiza os .txt de uma semana de estudos.")
    parser.add_argument("directory", type=Path, help="Pasta da semana com arquivos .txt em UTF-8")
    parser.add_argument("--output", type=Path, default=Path("output/sintese.md"), help="Markdown de destino (não sobrescreve)")
    parser.add_argument("--check", action="store_true", help="Valida entrada e configuração, sem chamada ou arquivo de saída")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    logger.setLevel(logging.INFO)
    try:
        config = Config.load()
        notes = read_notes(args.directory, config.max_input_chars)
        validate_output(args.directory, args.output)
        logger.info("Entrada validada: %d arquivos, %d caracteres.", len(notes), sum(len(n.text) for n in notes))
        if args.check:
            print("Entrada válida. Nenhuma chamada à API foi realizada.")
            return 0
        logger.info("Solicitando síntese ao LLM.")
        result = render_markdown(summarize(notes, config))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(result)
        print(result, end="")
        print(f"\nSalvo em: {args.output}")
        logger.info("Síntese concluída e salva.")
        return 0
    except AppError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except OSError:
        print("Erro: não foi possível salvar a saída. Verifique caminho, espaço e permissões.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExecução interrompida.", file=sys.stderr)
        return 130
