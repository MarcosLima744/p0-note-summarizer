import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import httpx

from note_summarizer.cli import main
from note_summarizer.config import AppError, Config
from note_summarizer.llm import summarize
from note_summarizer.notes import Note, read_notes
from note_summarizer.summary import Summary, render_markdown, validate_evidence


def sample_summary():
    return Summary.model_validate({
        "assuntos": [{"assunto": "Python", "sintese": "Estudo de escopo.",
                      "dificuldades": ["Closures"]}],
        "tarefas": [{"descricao": "Revisar closures", "conferir": False,
                     "referencias": [{"arquivo": "segunda.txt", "trecho": "Não entendi closures."}]}],
    })


class InputTests(unittest.TestCase):
    def test_sorted_direct_files_only_and_empty_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "b.txt").write_text("Segundo", encoding="utf-8")
            (folder / "a.txt").write_text("\ufeffPrimeiro", encoding="utf-8")
            (folder / "vazio.txt").write_text(" \n", encoding="utf-8")
            (folder / "ignorar.md").write_text("ignorar", encoding="utf-8")
            (folder / "sub").mkdir()
            (folder / "sub" / "oculto.txt").write_text("ignorar", encoding="utf-8")
            notes = read_notes(folder, 100)
            self.assertEqual([n.filename for n in notes], ["a.txt", "b.txt"])
            self.assertEqual(notes[0].text, "Primeiro")

    def test_rejects_empty_invalid_encoding_and_oversize(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            with self.assertRaisesRegex(AppError, "conteúdo útil"):
                read_notes(folder, 5)
            path = folder / "a.txt"
            path.write_bytes(b"\xff")
            with self.assertRaisesRegex(AppError, "UTF-8"):
                read_notes(folder, 5)
            path.write_text("abcdef", encoding="utf-8")
            with self.assertRaisesRegex(AppError, "excedem"):
                read_notes(folder, 5)
            path.write_text("abc", encoding="utf-8")
            (folder / "b.txt").write_text("def", encoding="utf-8")
            with self.assertRaisesRegex(AppError, "excedem"):
                read_notes(folder, 5)

    def test_symlink_is_not_sent(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "real.md").write_text("privado", encoding="utf-8")
            (folder / "link.txt").symlink_to(folder / "real.md")
            with self.assertRaisesRegex(AppError, "simbólico"):
                read_notes(folder, 100)


class ConfigTests(unittest.TestCase):
    def load(self, env):
        with patch.dict(os.environ, env, clear=True), patch("note_summarizer.config.load_dotenv"):
            return Config.load()

    def test_local_defaults_need_no_key(self):
        config = self.load({})
        self.assertEqual(config.model, "qwen3:4b-instruct")
        self.assertEqual(config.base_url, "http://localhost:11434")

    def test_invalid_limits(self):
        for name, value in [("OLLAMA_TIMEOUT", "nan"), ("OLLAMA_TIMEOUT", "-1"),
                            ("OLLAMA_MAX_OUTPUT_TOKENS", "abc"), ("NOTES_MAX_INPUT_CHARS", "0"),
                            ("OLLAMA_TEMPERATURE", "nan"), ("OLLAMA_TEMPERATURE", "-1"),
                            ("OLLAMA_CONTEXT_LENGTH", "100")]:
            with self.subTest(name=name, value=value), self.assertRaises(AppError):
                self.load({name: value})

    def test_rejects_invalid_or_remote_endpoints_and_cloud_model(self):
        for url in ["", "not-a-url", "https://ollama.com", "http://localhost:nope",
                    "http://localhost:0", "http://user:secret@localhost:11434", "http://localhost/api"]:
            with self.subTest(url=url), self.assertRaisesRegex(AppError, "endereço local"):
                self.load({"OLLAMA_BASE_URL": url})
        with self.assertRaisesRegex(AppError, "modelo local"):
            self.load({"OLLAMA_MODEL": "qwen3:cloud"})

    def test_accepts_ipv6_loopback(self):
        self.assertEqual(self.load({"OLLAMA_BASE_URL": "http://[::1]:11434/"}).base_url,
                         "http://[::1]:11434")


class ResponseTests(unittest.TestCase):
    def test_references_must_be_literal_and_known(self):
        summary = sample_summary()
        notes = [Note("segunda.txt", "Não entendi closures.")]
        validate_evidence(summary, notes)
        summary.tarefas[0].referencias[0].trecho = "trecho inventado"
        with self.assertRaisesRegex(AppError, "referência inexistente"):
            validate_evidence(summary, notes)
        summary.tarefas[0].referencias[0].trecho = "Não entendi closures."
        summary.tarefas[0].referencias[0].arquivo = "inventado.txt"
        with self.assertRaises(AppError):
            validate_evidence(summary, notes)

    def test_no_tasks_and_ambiguity_rendering(self):
        summary = sample_summary()
        summary.tarefas[0].conferir = True
        self.assertIn("Conferir", render_markdown(summary))
        self.assertIn("segunda.txt", render_markdown(summary))
        summary.tarefas = []
        self.assertIn("Nenhuma tarefa identificada.", render_markdown(summary))

    def call_api(self, status=200, body=None):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(status, json=body)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch("note_summarizer.llm.httpx.Client", return_value=client) as factory:
            result = summarize([Note("segunda.txt", "Não entendi closures.")], Config())
            factory.assert_called_once_with(timeout=300, trust_env=False)
        return result, requests

    def api_body(self, text):
        return {"model": "qwen3:4b-instruct", "done": True, "done_reason": "stop",
                "message": {"role": "assistant", "content": text}}

    def test_http_serialization_and_parsing_without_network(self):
        result, requests = self.call_api(body=self.api_body(sample_summary().model_dump_json()))
        self.assertEqual(result, sample_summary())
        self.assertEqual(len(requests), 1)
        self.assertEqual(str(requests[0].url), "http://localhost:11434/api/chat")
        self.assertNotIn("authorization", requests[0].headers)
        payload = json.loads(requests[0].content)
        self.assertEqual(payload["model"], "qwen3:4b-instruct")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"], Summary.model_json_schema())
        self.assertEqual(payload["options"]["num_ctx"], 32768)
        self.assertIn("Não entendi closures.", payload["messages"][1]["content"])

    def test_api_failures_are_readable_and_do_not_echo_server_details(self):
        for code, expected in [(401, "credencial"), (403, "credencial"), (404, "ollama pull"),
                               (503, "indisponível"), (400, "parâmetros")]:
            with self.subTest(code=code), self.assertRaisesRegex(AppError, expected) as raised:
                self.call_api(code, {"error": "test-secret"})
            self.assertNotIn("test-secret", str(raised.exception))

    def test_malformed_empty_incomplete_and_error_responses(self):
        bodies = [self.api_body("not json"), self.api_body(""),
                  {**self.api_body("{}"), "done": False},
                  {**self.api_body("{}"), "done_reason": "length"},
                  {**self.api_body("{}"), "message": None},
                  {"error": "test-secret"}, [],
                  self.api_body("Não posso responder.")]
        for body in bodies:
            with self.subTest(body=body), self.assertRaises(AppError):
                self.call_api(body=body)

    def test_network_and_timeout(self):
        for error, expected in [(httpx.ConnectError, "conectar"), (httpx.ReadTimeout, "tempo limite")]:
            def handler(request):
                raise error("test-secret", request=request)
            client = httpx.Client(transport=httpx.MockTransport(handler))
            with patch("note_summarizer.llm.httpx.Client", return_value=client):
                with self.assertRaisesRegex(AppError, expected):
                    summarize([Note("a.txt", "conteúdo")], Config())


class CliTests(unittest.TestCase):
    def test_cli_saves_mocked_result_and_refuses_overwrite_or_output_in_input(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "semana"
            folder.mkdir()
            (folder / "segunda.txt").write_text("Não entendi closures.", encoding="utf-8")
            output = Path(root) / "result.md"
            with patch("note_summarizer.cli.Config.load", return_value=Config()), \
                 patch("note_summarizer.cli.summarize", return_value=sample_summary()) as mocked, \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(folder), "--output", str(output)]), 0)
                self.assertIn("Revisar closures", output.read_text(encoding="utf-8"))
                self.assertEqual(main([str(folder), "--output", str(output)]), 1)
                self.assertEqual(main([str(folder), "--output", str(folder / "result.md")]), 1)
                self.assertEqual(mocked.call_count, 1)

    def test_check_has_no_api_call_and_no_output(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "semana"
            folder.mkdir()
            (folder / "a.txt").write_text("Estudei Python.", encoding="utf-8")
            output = Path(root) / "result.md"
            with patch("note_summarizer.cli.Config.load", return_value=Config()), \
                 patch("note_summarizer.cli.summarize") as mocked, redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(folder), "--output", str(output), "--check"]), 0)
                mocked.assert_not_called()
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
