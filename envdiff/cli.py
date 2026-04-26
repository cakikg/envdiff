"""Command-line interface for envdiff.

Provides the main entry point and argument parsing for comparing
.env files across environments.
"""

import argparse
import sys
from pathlib import Path

from envdiff.core import compare_env_files, compare_multiple


ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_CYAN = "\033[96m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def supports_color() -> bool:
    """Check if the terminal supports ANSI color codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def colorize(text: str, color: str, use_color: bool = True) -> str:
    """Wrap text in ANSI color codes if color is enabled."""
    if use_color and supports_color():
        return f"{color}{text}{ANSI_RESET}"
    return text


def print_pairwise_diff(result: dict, use_color: bool = True) -> None:
    """Print a human-readable diff between two .env files."""
    file_a = result["files"][0]
    file_b = result["files"][1]

    print(colorize(f"\nComparing: {file_a}  <>  {file_b}", ANSI_BOLD, use_color))
    print("-" * 60)

    missing_in_b = result.get("missing_in", {}).get(file_b, [])
    missing_in_a = result.get("missing_in", {}).get(file_a, [])
    mismatched = result.get("mismatched", {})

    if not missing_in_a and not missing_in_b and not mismatched:
        print(colorize("  No differences found.", ANSI_GREEN, use_color))
        return

    if missing_in_b:
        print(colorize(f"  Keys in {Path(file_a).name} but missing in {Path(file_b).name}:", ANSI_YELLOW, use_color))
        for key in sorted(missing_in_b):
            print(f"    - {key}")

    if missing_in_a:
        print(colorize(f"  Keys in {Path(file_b).name} but missing in {Path(file_a).name}:", ANSI_YELLOW, use_color))
        for key in sorted(missing_in_a):
            print(f"    + {key}")

    if mismatched:
        print(colorize("  Keys with mismatched values:", ANSI_RED, use_color))
        for key, values in sorted(mismatched.items()):
            val_a = values.get(file_a, "<missing>")
            val_b = values.get(file_b, "<missing>")
            print(f"    ~ {key}")
            print(f"        {Path(file_a).name}: {val_a}")
            print(f"        {Path(file_b).name}: {val_b}")


def print_multi_diff(result: dict, use_color: bool = True) -> None:
    """Print a human-readable diff across multiple .env files."""
    files = result["files"]
    short_names = [Path(f).name for f in files]

    print(colorize(f"\nComparing {len(files)} files: {', '.join(short_names)}", ANSI_BOLD, use_color))
    print("-" * 60)

    missing = result.get("missing_in", {})
    mismatched = result.get("mismatched", {})

    if not any(missing.values()) and not mismatched:
        print(colorize("  No differences found.", ANSI_GREEN, use_color))
        return

    for file_path, keys in missing.items():
        if keys:
            print(colorize(f"  Missing in {Path(file_path).name}:", ANSI_YELLOW, use_color))
            for key in sorted(keys):
                print(f"    - {key}")

    if mismatched:
        print(colorize("  Keys with inconsistent values across files:", ANSI_RED, use_color))
        for key, values in sorted(mismatched.items()):
            print(f"    ~ {key}")
            for file_path, val in values.items():
                print(f"        {Path(file_path).name}: {val}")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments and highlight missing or mismatched keys.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if differences are found (useful for CI).",
    )
    return parser


def main() -> None:
    """Main entry point for the envdiff CLI."""
    parser = build_parser()
    args = parser.parse_args()
    use_color = not args.no_color

    if len(args.files) < 2:
        parser.error("At least two .env files are required.")

    for filepath in args.files:
        if not Path(filepath).exists():
            print(colorize(f"Error: File not found: {filepath}", ANSI_RED, use_color), file=sys.stderr)
            sys.exit(2)

    if len(args.files) == 2:
        result = compare_env_files(args.files[0], args.files[1])
        print_pairwise_diff(result, use_color=use_color)
        has_diff = bool(
            result.get("mismatched")
            or any(result.get("missing_in", {}).values())
        )
    else:
        result = compare_multiple(args.files)
        print_multi_diff(result, use_color=use_color)
        has_diff = bool(
            result.get("mismatched")
            or any(result.get("missing_in", {}).values())
        )

    print()

    if args.exit_code and has_diff:
        sys.exit(1)


if __name__ == "__main__":
    main()
