import argparse, json, os, re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from research_extractor.extractor.research_value_extractor import ResearchValueExtractor
from research_extractor.prompts.builder import PromptBuilder
from research_extractor.source.abstract import AbstractSource
from research_extractor.source.pdf import PDFSource
from research_extractor.util.utils import (
    get_text_files_from_directory,
    get_xml_files_from_directory,
    get_xml_pdf_pairs_from_directory,
    get_pdf_file_for_xml,
)
from research_extractor.extractor.research_value_extractor import (
    LLMClient,
)
from research_extractor.extractor.research_value_extractor import (
    ResponseJSONDecoder,
)
from research_extractor.table_extractor.table_extractor import TableExtractor

# Import evaluation functionality
try:
    from research_extractor.eval.evaluate_completeness import FieldCompletenessEvaluator

    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False
    print("Warning: Evaluation module not available. Install required dependencies.")


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
        # Get XML files and their corresponding PDF files
        xml_pdf_pairs = get_xml_pdf_pairs_from_directory(input_path)
        
        # Initialize table extractor (reused for all files)
        table_extractor = TableExtractor()
        print("here")
        for xml_file, pdf_file in xml_pdf_pairs:
            print(pdf_file.exists())
            src = PDFSource(str(xml_file))
            
            # Extract table images  from PDF if PDF file exists
            extracted_table_binaries = []
            if pdf_file and pdf_file.exists():
                print("exist")
                extracted_tables = table_extractor.extract_from_pdf(
                    str(pdf_file), 
                    threshold=0.9, 
                    padding=20
                )
                print(extracted_tables[0].keys())
            
            pb = PromptBuilder(
                doc=src.load(), 
                fields=fields, 
                extracted_tables=extracted_tables
            )
            extractor = ResearchValueExtractor(
                llm_client=llm, prompt_builder=pb, decoder=decoder
            )
            rec_id = xml_file.stem  # Use filename as ID
            try:
                out = extractor.extract()
                out = {"input_id": rec_id, **out} if rec_id else out
                # Add extracted table binary data
                if extracted_table_binaries:
                    out["extracted_tables"] = extracted_table_binaries
                n_ok += 1
            except Exception as e:
                out = {"input_id": rec_id, "error": str(e)}
                # Add extracted table binary data even if extraction failed
                if extracted_table_binaries:
                    out["extracted_tables"] = extracted_table_binaries
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


def run_evaluation(
    results_file: Path, output_dir: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """Run field completeness evaluation on the generated results file."""
    if not EVALUATION_AVAILABLE:
        print("Evaluation not available. Skipping completeness analysis.")
        return None

    if not results_file.exists():
        print(f"Results file not found: {results_file}. Skipping evaluation.")
        return None

    print(f"\n{'='*60}")
    print("RUNNING FIELD COMPLETENESS EVALUATION")
    print(f"{'='*60}")

    try:
        evaluator = FieldCompletenessEvaluator(str(results_file))
        stats = evaluator.run_evaluation(
            create_plots=False, export_results=True  # Skip plots for automated runs
        )

        if stats and "overall_completeness" in stats:
            print(f"\nEvaluation completed successfully!")
            print(f"Overall completeness: {stats['overall_completeness']:.2f}%")
            return stats
        else:
            print("Evaluation completed but no statistics returned.")
            return None

    except Exception as e:
        print(f"Error during evaluation: {e}")
        return None


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
    ap.add_argument(
        "--no-eval",
        action="store_true",
        help="Skip running field completeness evaluation after extraction",
        default=True,
    )
    ap.add_argument(
        "--eval-output-dir",
        type=Path,
        default=Path("evaluation_outputs"),
        help="Directory to save evaluation outputs (default: evaluation_outputs)",
    )
    ap.add_argument(
        "--eval-flag",
        help="Flag to enable evaluation",
        default=False
    )
    args = ap.parse_args()

    # Run the extraction process
    metrics = run(args.input, args.output, args.provider, args.fields, args.input_type)

    # Generate summary report
    summary = f"# Run summary\n- Inputs: {metrics['n_inputs']}\n- OK: {metrics['n_ok']}\n- Provider: {metrics['provider']}\n- Input Type: {metrics['input_type']}\n- Output: `{args.output}`\n"
    Path("research_extractor/outputs").mkdir(exist_ok=True)
    Path(f"research_extractor/outputs/report-{args.provider}.md").write_text(
        summary, encoding="utf-8"
    )
    Path(f"research_extractor/outputs/metrics-{args.provider}.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )

    # Run evaluation if not disabled
    evaluation_stats = None
    if not args.no_eval:
        evaluation_stats = run_evaluation(args.output, args.eval_output_dir)

        # Add evaluation results to summary if available
        if evaluation_stats:
            summary += f"- Overall Completeness: {evaluation_stats['overall_completeness']:.2f}%\n"
            
            # Add per-study completeness statistics
            per_study_stats = evaluation_stats.get('per_study_completeness', [])
            if per_study_stats:
                completeness_rates = [study['completeness_rate'] for study in per_study_stats]
                avg_study_completeness = sum(completeness_rates) / len(completeness_rates) * 100
                studies_100_percent = sum(1 for rate in completeness_rates if rate == 1.0)
                studies_80_plus = sum(1 for rate in completeness_rates if rate >= 0.8)
                
                summary += f"- Average Study Completeness: {avg_study_completeness:.2f}%\n"
                summary += f"- Studies with 100% completeness: {studies_100_percent}/{len(per_study_stats)}\n"
                summary += f"- Studies with 80%+ completeness: {studies_80_plus}/{len(per_study_stats)}\n"
            
            summary += f"- Evaluation Results: detailed_completeness_analysis.json\n"

            # Update the report with evaluation results
            Path(f"research_extractor/outputs/report-{args.provider}.md").write_text(
                summary, encoding="utf-8"
            )

    # Final summary
    print(f"\n{'='*60}")
    print("EXPERIMENT COMPLETED")
    print(f"{'='*60}")
    print(f"Extraction Results:")
    print(f"  - Total inputs: {metrics['n_inputs']}")
    print(f"  - Successful extractions: {metrics['n_ok']}")
    print(f"  - Success rate: {(metrics['n_ok']/metrics['n_inputs']*100):.1f}%")
    print(f"  - Output file: {args.output}")

    if evaluation_stats:
        print(f"\nEvaluation Results:")
        print(
            f"  - Overall completeness: {evaluation_stats['overall_completeness']:.2f}%"
        )
        
        # Add per-study completeness to console output
        per_study_stats = evaluation_stats.get('per_study_completeness', [])
        if per_study_stats:
            completeness_rates = [study['completeness_rate'] for study in per_study_stats]
            avg_study_completeness = sum(completeness_rates) / len(completeness_rates) * 100
            studies_100_percent = sum(1 for rate in completeness_rates if rate == 1.0)
            studies_80_plus = sum(1 for rate in completeness_rates if rate >= 0.8)
            
            print(f"  - Average study completeness: {avg_study_completeness:.2f}%")
            print(f"  - Studies with 100% completeness: {studies_100_percent}/{len(per_study_stats)}")
            print(f"  - Studies with 80%+ completeness: {studies_80_plus}/{len(per_study_stats)}")
        
        print(f"  - Detailed analysis: detailed_completeness_analysis.json")
    elif not args.no_eval:
        print(f"\nEvaluation: Skipped (evaluation not available)")
    else:
        print(f"\nEvaluation: Disabled by user")


if __name__ == "__main__":
    main()
