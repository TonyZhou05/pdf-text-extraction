#!/usr/bin/env python3
"""
Evaluation script to calculate the completeness of extracted fields from results-pdf-azure.jsonl

This script analyzes the completeness of field extraction by:
1. Counting total records and fields
2. Calculating completeness percentage for each field
3. Identifying which fields are most/least complete
4. Providing detailed statistics and visualizations


### Basic Usage
```bash
python evaluate_completeness.py research_extractor/outputs/results-pdf-azure.jsonl
```

### Command Line Options
```bash
python evaluate_completeness.py [OPTIONS] results_file

Options:
  --no-plots          Skip creating visualization plots
  --no-export         Skip exporting detailed results
  --output-dir DIR    Directory to save output files (default: evaluation_outputs)
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any

# Optional imports for visualization
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    print(
        "Warning: Visualization libraries not available. Install matplotlib, seaborn, and pandas for plotting."
    )


class FieldCompletenessEvaluator:
    """Evaluates the completeness of extracted fields from JSONL results."""

    def __init__(self, results_file: str):
        """Initialize the evaluator with a results file."""
        self.results_file = Path(results_file)
        self.data = []
        self.field_names = [
            "Study Name",
            "Study Type",
            "Study Year",
            "Location",
            "Phase",
            "Conditions",
            "Treatments",
            "Comparator",
            "Num Patients",
            "Mean Age",
            "Age Range",
        ]
        self.load_data()

    def load_data(self):
        """Load and parse the JSONL results file."""
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")

        print(f"Loading data from {self.results_file}...")
        with open(self.results_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    self.data.append(record)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON on line {line_num}: {e}")
                    continue

        print(f"Loaded {len(self.data)} records")

    def is_field_complete(self, field_value: str) -> bool:
        """Check if a field value is considered complete (not 'NP' or empty)."""
        if not field_value or field_value.strip() == "":
            return False
        if field_value.strip().upper() == "NP":
            return False
        return True

    def calculate_completeness(self) -> Dict[str, Any]:
        """Calculate completeness statistics for all fields."""
        if not self.data:
            return {"error": "No data loaded"}

        total_records = len(self.data)
        field_stats = {}

        # Initialize counters for each field
        for field_name in self.field_names:
            field_stats[field_name] = {
                "complete": 0,
                "incomplete": 0,
                "completeness_percentage": 0.0,
                "values": [],
            }

        # Analyze each record
        for record in self.data:
            if "result" not in record:
                continue

            # Create a dictionary of field values for easy lookup
            field_values = {}
            for field in record["result"]:
                if "name" in field and "value" in field:
                    field_values[field["name"]] = field["value"]

            # Check completeness for each expected field
            for field_name in self.field_names:
                value = field_values.get(field_name, "")
                is_complete = self.is_field_complete(value)

                if is_complete:
                    field_stats[field_name]["complete"] += 1
                    field_stats[field_name]["values"].append(value)
                else:
                    field_stats[field_name]["incomplete"] += 1

        # Calculate percentages
        for field_name in self.field_names:
            complete = field_stats[field_name]["complete"]
            field_stats[field_name]["completeness_percentage"] = (
                complete / total_records
            ) * 100

        return {
            "total_records": total_records,
            "field_stats": field_stats,
            "overall_completeness": self._calculate_overall_completeness(
                field_stats, total_records
            ),
            "per_study_completeness": self._calculate_per_study_completeness(),
        }

    def _calculate_per_study_completeness(self):
        per_study = []
        for record in self.data:
            input_id = record.get("input_id")
            if "result" not in record:
                continue
            filled = 0
            for field in record["result"]:
                if "name" in field and "value" in field:
                    if self.is_field_complete(field["value"]):
                        filled += 1
            total = len(self.field_names)
            per_study.append({
                "input_id": input_id,
                "completeness_rate": filled / total
            })
        return per_study

    def _calculate_overall_completeness(
        self, field_stats: Dict, total_records: int
    ) -> float:
        """Calculate overall completeness across all fields."""
        total_possible_fields = len(self.field_names) * total_records
        total_complete_fields = sum(stats["complete"] for stats in field_stats.values())
        return (total_complete_fields / total_possible_fields) * 100

    def get_field_ranking(self, stats: Dict) -> List[Tuple[str, float]]:
        """Get fields ranked by completeness percentage."""
        field_stats = stats["field_stats"]
        ranking = [
            (field, field_stats[field]["completeness_percentage"])
            for field in self.field_names
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)
    
    def get_per_study_stats(self, stats: Dict) -> Dict[str, Any]:
        """Calculate per-study completeness statistics."""
        per_study = stats.get("per_study_completeness", [])
        if not per_study:
            return {}
        
        completeness_rates = [study["completeness_rate"] for study in per_study]
        
        return {
            "total_studies": len(per_study),
            "avg_completeness": sum(completeness_rates) / len(completeness_rates) * 100,
            "min_completeness": min(completeness_rates) * 100,
            "max_completeness": max(completeness_rates) * 100,
            "studies_100_percent": sum(1 for rate in completeness_rates if rate == 1.0),
            "studies_80_plus": sum(1 for rate in completeness_rates if rate >= 0.8),
            "studies_50_plus": sum(1 for rate in completeness_rates if rate >= 0.5),
            "studies_below_50": sum(1 for rate in completeness_rates if rate < 0.5),
        }

    def print_summary(self, stats: Dict):
        """Print a summary of completeness statistics."""
        print("\n" + "=" * 80)
        print("FIELD COMPLETENESS EVALUATION SUMMARY")
        print("=" * 80)

        print(f"Total Records: {stats['total_records']}")
        print(f"Overall Completeness: {stats['overall_completeness']:.2f}%")
        print(f"Total Fields Analyzed: {len(self.field_names)}")

        # Add per-study statistics
        per_study_stats = self.get_per_study_stats(stats)
        if per_study_stats:
            print(f"\nPer-Study Completeness Statistics:")
            print("-" * 50)
            print(f"Average Study Completeness: {per_study_stats['avg_completeness']:.2f}%")
            print(f"Min Study Completeness: {per_study_stats['min_completeness']:.2f}%")
            print(f"Max Study Completeness: {per_study_stats['max_completeness']:.2f}%")
            print(f"Studies with 100% completeness: {per_study_stats['studies_100_percent']}/{per_study_stats['total_studies']}")
            print(f"Studies with 80%+ completeness: {per_study_stats['studies_80_plus']}/{per_study_stats['total_studies']}")
            print(f"Studies with 50%+ completeness: {per_study_stats['studies_50_plus']}/{per_study_stats['total_studies']}")
            print(f"Studies below 50% completeness: {per_study_stats['studies_below_50']}/{per_study_stats['total_studies']}")


        print("\nDetailed Field Statistics:")
        print("-" * 50)
        field_stats = stats["field_stats"]
        for field in self.field_names:
            stats_data = field_stats[field]
            print(
                f"{field:<15}: {stats_data['complete']:3d}/{stats['total_records']:3d} "
                f"({stats_data['completeness_percentage']:6.2f}%)"
            )

    def print_detailed_analysis(self, stats: Dict):
        """Print detailed analysis including sample values."""
        print("\n" + "=" * 80)
        print("DETAILED FIELD ANALYSIS")
        print("=" * 80)

        field_stats = stats["field_stats"]

        for field in self.field_names:
            stats_data = field_stats[field]
            print(f"\n{field}:")
            print(f"  Completeness: {stats_data['completeness_percentage']:.2f}%")
            print(f"  Complete: {stats_data['complete']}/{stats['total_records']}")

            # Show sample values for complete fields
            if stats_data["values"]:
                print(f"  Sample values: {', '.join(stats_data['values'][:5])}")
                if len(stats_data["values"]) > 5:
                    print(f"  ... and {len(stats_data['values']) - 5} more")

    def create_visualization(self, stats: Dict, output_dir: str = "evaluation_outputs"):
        """Create visualization charts for the completeness data."""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Prepare data for plotting
        field_names = list(stats["field_stats"].keys())
        completeness_values = [
            stats["field_stats"][field]["completeness_percentage"]
            for field in field_names
        ]

        # Set up the plotting style
        plt.style.use("default")
        sns.set_palette("husl")

        # Create completeness bar chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # Bar chart
        bars = ax1.bar(
            range(len(field_names)),
            completeness_values,
            color=[
                "green" if x >= 80 else "orange" if x >= 50 else "red"
                for x in completeness_values
            ],
        )
        ax1.set_xlabel("Fields")
        ax1.set_ylabel("Completeness Percentage")
        ax1.set_title("Field Completeness Overview")
        ax1.set_xticks(range(len(field_names)))
        ax1.set_xticklabels(field_names, rotation=45, ha="right")
        ax1.set_ylim(0, 100)
        ax1.grid(axis="y", alpha=0.3)

        # Add percentage labels on bars
        for i, (bar, value) in enumerate(zip(bars, completeness_values)):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        # Horizontal bar chart for better readability
        y_pos = range(len(field_names))
        bars2 = ax2.barh(
            y_pos,
            completeness_values,
            color=[
                "green" if x >= 80 else "orange" if x >= 50 else "red"
                for x in completeness_values
            ],
        )
        ax2.set_xlabel("Completeness Percentage")
        ax2.set_ylabel("Fields")
        ax2.set_title("Field Completeness (Horizontal)")
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(field_names)
        ax2.set_xlim(0, 100)
        ax2.grid(axis="x", alpha=0.3)

        # Add percentage labels
        for i, (bar, value) in enumerate(zip(bars2, completeness_values)):
            ax2.text(
                bar.get_width() + 1,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.1f}%",
                ha="left",
                va="center",
                fontsize=9,
            )

        plt.tight_layout()
        plt.savefig(
            output_path / "field_completeness.png", dpi=300, bbox_inches="tight"
        )
        plt.show()

        # Create a summary table
        self._create_summary_table(stats, output_path)

        print(f"\nVisualizations saved to: {output_path}")

    def _create_summary_table(self, stats: Dict, output_path: Path):
        """Create a summary table as CSV."""
        if not HAS_VISUALIZATION:
            # Create a simple CSV without pandas
            csv_file = output_path / "completeness_summary.csv"
            with open(csv_file, "w") as f:
                f.write("Field,Complete,Incomplete,Total,Completeness_Percentage\n")
                for field in self.field_names:
                    field_stats = stats["field_stats"][field]
                    f.write(
                        f"{field},{field_stats['complete']},{field_stats['incomplete']},"
                        f"{stats['total_records']},{field_stats['completeness_percentage']:.2f}\n"
                    )
            print(f"Summary table saved to: {csv_file}")
            return

        data = []
        for field in self.field_names:
            field_stats = stats["field_stats"][field]
            data.append(
                {
                    "Field": field,
                    "Complete": field_stats["complete"],
                    "Incomplete": field_stats["incomplete"],
                    "Total": stats["total_records"],
                    "Completeness_Percentage": field_stats["completeness_percentage"],
                }
            )

        df = pd.DataFrame(data)
        df = df.sort_values("Completeness_Percentage", ascending=False)
        df.to_csv(output_path / "completeness_summary.csv", index=False)

        print(f"Summary table saved to: {output_path / 'completeness_summary.csv'}")

    def export_detailed_results(
        self, stats: Dict, output_file: str = "detailed_completeness_analysis.json"
    ):
        """Export detailed results to JSON file."""

        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            elif hasattr(obj, "item"):  # numpy scalar
                return obj.item()
            else:
                return obj

        export_data = convert_types(stats)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"Detailed results exported to: {output_file}")

    def run_evaluation(self, create_plots: bool = True, export_results: bool = True):
        """Run the complete evaluation process."""
        print("Starting field completeness evaluation...")

        # Calculate statistics
        stats = self.calculate_completeness()

        if "error" in stats:
            print(f"Error: {stats['error']}")
            return

        # Print summary
        self.print_summary(stats)

        # Print detailed analysis
        self.print_detailed_analysis(stats)

        # Create visualizations
        if create_plots:
            try:
                self.create_visualization(stats)
            except ImportError as e:
                print(
                    f"Warning: Could not create plots due to missing dependencies: {e}"
                )
                print(
                    "Install matplotlib and seaborn to enable plotting: pip install matplotlib seaborn"
                )

        # Export results
        if export_results:
            self.export_detailed_results(stats)

        return stats


def main():
    """Main function to run the evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate field completeness in extraction results"
    )
    parser.add_argument("results_file", help="Path to the results JSONL file")
    parser.add_argument(
        "--no-plots", action="store_true", help="Skip creating visualization plots"
    )
    parser.add_argument(
        "--no-export", action="store_true", help="Skip exporting detailed results"
    )
    parser.add_argument(
        "--output-dir",
        default="evaluation_outputs",
        help="Directory to save output files (default: evaluation_outputs)",
    )

    args = parser.parse_args()

    try:
        evaluator = FieldCompletenessEvaluator(args.results_file)
        stats = evaluator.run_evaluation(
            create_plots=not args.no_plots, export_results=not args.no_export
        )

        print("\n" + "=" * 80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        print(f"Error running evaluation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
