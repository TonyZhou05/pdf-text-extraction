import argparse, json, os, re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from research_extractor.extractor.research_value_extractor import ResearchValueExtractor
from research_extractor.prompts.builder import PromptBuilder
from research_extractor.source.abstract import AbstractSource
from research_extractor.source.pdf import PDFSource
from research_extractor.util.utils import get_text_files_from_directory
from research_extractor.extractor.research_value_extractor import (
    LLMClient,
)  # your Protocol if present
from research_extractor.extractor.research_value_extractor import (
    ResponseJSONDecoder,
)  # if exported


# -------- dataset IO --------
def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            yield json.loads(line)


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# Fake LLM for offline testing
class FakeLLMClient(LLMClient):
    """Offline stub: returns a tiny JSON derived by regex on the prompt text."""

    def chat(self, messages: str, **kwargs) -> str:

        return json.dumps(
            {
                "title": None,
                "year": "2020",
                "study_type": "dummy type",
                "sample_size": "100",
            }
        )


def get_llm(provider: str) -> LLMClient:
    provider = provider.lower()
    model = os.getenv("MODEL_NAME", "gpt-4o")

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            from research_extractor.llm.openai import OpenAIClient

            return OpenAIClient(model=model)
        except ImportError:
            print("Warning: OpenAI client not available, using fake client")
            return FakeLLMClient()

    if (
        provider == "azure"
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
    ):
        try:
            from research_extractor.llm.azure import AzureOpenAIClient

            return AzureOpenAIClient(model=model)
        except ImportError as e:
            print(f"Warning: Azure client not available, using fake client: {e}")
            return FakeLLMClient()

    return FakeLLMClient()


def run(
    input_path: Path,
    out_path: Path,
    provider: str,
    fields: Optional[List[str]] = None,
    input_type: str = "abstract",
) -> Dict[str, Any]:
    llm = get_llm(provider=provider)
    decoder = ResponseJSONDecoder()
    results: List[Dict[str, Any]] = []
    n_ok = 0

    if input_type == "abstract_jsonl":
        # Process JSONL file with abstracts
        for rec in read_jsonl(input_path):
            src = AbstractSource(
                abstract=rec.get("abstract", ""),
                title=rec.get("title", "") or "",
                year=str(rec.get("year", "") or ""),
                pub_type=rec.get("publication_type", "") or "",
            )
            pb = PromptBuilder(doc=src.load(), fields=fields)
            extractor = ResearchValueExtractor(
                llm_client=llm, prompt_builder=pb, decoder=decoder
            )
            rec_id = rec.get("id", "unknown")
            try:
                out = extractor.extract()
                out = {"input_id": rec_id, **out} if rec_id else out
                n_ok += 1
            except Exception as e:
                out = {"input_id": rec_id, "error": str(e)}
            results.append(out)

    elif input_type == "pdf_text_dir":
        # Process text files using PDFSource
        text_files = get_text_files_from_directory(input_path)
        for text_file in text_files:
            src = PDFSource(str(text_file))
            pb = PromptBuilder(doc=src.load(), fields=fields)
            extractor = ResearchValueExtractor(
                llm_client=llm, prompt_builder=pb, decoder=decoder
            )
            rec_id = text_file.stem  # Use filename as ID
            try:
                out = extractor.extract()
                out = {"input_id": rec_id, **out} if rec_id else out
                n_ok += 1
            except Exception as e:
                out = {"input_id": rec_id, "error": str(e)}
            results.append(out)

    else:
        raise ValueError(
            f"Invalid input_type: {input_type}. Must be 'jsonl' or 'text_dir'"
        )

    write_jsonl(out_path, results)
    return {
        "n_inputs": len(results),
        "n_ok": n_ok,
        "provider": provider,
        "input_type": input_type,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input path: JSONL file containing abstracts OR directory containing text files",
    )
    ap.add_argument("--output", type=Path, default=Path("outputs/results.jsonl"))
    ap.add_argument(
        "--provider",
        choices=["fake", "openai", "azure"],
        default=os.getenv("API_PROVIDER", "fake"),
    )
    ap.add_argument("--fields", nargs="*", help="Optional list of fields to extract")
    ap.add_argument(
        "--input-type",
        choices=["abstract_jsonl", "pdf_text_dir"],
        default="abstract_jsonl",
        help="Type of input: 'abstract_jsonl' for abstract metadata file, 'pdf_text_dir' for directory of text files",
    )
    args = ap.parse_args()
    metrics = run(args.input, args.output, args.provider, args.fields, args.input_type)
    # lightweight run summary for CI
    summary = f"# Run summary\n- Inputs: {metrics['n_inputs']}\n- OK: {metrics['n_ok']}\n- Provider: {metrics['provider']}\n- Input Type: {metrics['input_type']}\n- Output: `{args.output}`\n"
    Path("research_extractor/outputs").mkdir(exist_ok=True)
    Path(f"research_extractor/outputs/report-{args.provider}.md").write_text(
        summary, encoding="utf-8"
    )
    Path(f"research_extractor/outputs/metrics-{args.provider}.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
