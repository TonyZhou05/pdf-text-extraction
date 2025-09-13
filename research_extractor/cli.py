import argparse, json, os

from .llm.azureOpenAIClient import AzureOpenAIClient
from .llm.openai import OpenAIClient
from .extractor.research_value_extractor import ResearchValueExtractor
from .prompts.builder import PromptBuilder
from .source.abstract import AbstractSource


def build_parser():
    parser = argparse.ArgumentParser(
        description="Extract structured values from research papers"
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--abstract", type=str, help="Abstract text to extract from"
    )
    input_group.add_argument("--pdf", type=str, help="Path to PDF file to extract from")

    # Extraction options
    parser.add_argument(
        "--fields",
        type=str,
        nargs="+",
        help="Fields to extract (if not provided, uses default fields)",
    )
    parser.add_argument(
        "--single-field", type=str, help="Extract a single field (provide description)"
    )

    # Paper metadata (for abstract extraction)
    parser.add_argument("--title", type=str, default="", help="Paper title")
    parser.add_argument("--year", type=str, default="", help="Publication year")
    parser.add_argument(
        "--publication-type", type=str, default="", help="Publication type"
    )

    # Output options
    parser.add_argument("--output", type=str, help="Output file path (JSON format)")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty print JSON output"
    )

    # API options
    parser.add_argument(
        "--provider", choices=["openai", "azure"], default="azure", help="API provider"
    )
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    parser.add_argument(
        "--model", type=str, default="gpt-4o", help="OpenAI model to use"
    )

    return parser


def _parse_from_args(args):
    if args.single_field:
        fields = [args.single_field]
    elif args.fields:
        fields = args.fields
    else:
        fields = None

    return fields


def _llm_client_from_args(args):
    if args.provider == "openai":
        return OpenAIClient(model=args.model)
    return AzureOpenAIClient(model=args.model)


def main():
    parser = build_parser()
    args = parser.parse_args()

    # parse llm and fields arguments
    llm_client = _llm_client_from_args(args)
    fields = _parse_from_args(args)
    if args.abstract:
        source = AbstractSource(
            abstract=args.abstract,
            title=args.title,
            year=args.year,
            pub_type=args.publication_type,
        )
    else:
        # source = PDFSource(file_path=args.pdf)
        raise NotImplementedError("PDF source not implemented yet.")

    prompt_builder = PromptBuilder(doc=source.load(), fields=fields)
    extractor = ResearchValueExtractor(
        llm_client=llm_client, prompt_builder=prompt_builder
    )
    res = extractor.extract()
    # print(res)


if __name__ == "__main__":
    exit(main())
