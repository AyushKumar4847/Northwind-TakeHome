"""
Northwind Group Consolidation - Main Entry Point (main.py)

Usage:
    python main.py
"""

from pathlib import Path
from src.pipeline import run_pipeline


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "data" / "input"
    if not input_dir.exists():
        input_dir = base_dir / "data"

    output_dir = base_dir / "data" / "output"
    run_pipeline(input_dir, output_dir)


if __name__ == "__main__":
    main()

