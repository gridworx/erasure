"""Entry point for erasure-ctl."""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="erasure-ctl",
        description="Secure disk erasure with branded certificate generation",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Path to data directory containing config CSVs, logo, and reports",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run with mock data (for development/testing without real drives)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()

    from erasure_ctl.core.runtime import detect_runtime
    from erasure_ctl.tui.app import ErasureApp

    runtime = detect_runtime(data_dir=args.data_dir)
    app = ErasureApp(runtime=runtime, mock=args.mock)
    app.run()


from erasure_ctl import __version__  # noqa: E402

if __name__ == "__main__":
    main()
