from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from appium_tests.utils.report_utils import write_excel_report


def run_demo_report(output_path: str | None = None) -> Path:
    output = output_path or str(Path(__file__).resolve().parent / "reports" / "appium_e2e_report.xlsx")
    rows = [
        {
            "test_name": "launch_app",
            "status": "passed",
            "duration": 3.5,
            "message": "App initialized successfully",
        },
        {
            "test_name": "login_flow",
            "status": "passed",
            "duration": 5.2,
            "message": "Login form detected",
        },
    ]
    return write_excel_report(rows, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a sample Excel report for Appium E2E tests")
    parser.add_argument("--demo", action="store_true", help="Generate a demo Excel report")
    parser.add_argument("--output", type=str, default=None, help="Custom output path for the Excel report")
    args = parser.parse_args()

    if args.demo:
        path = run_demo_report(args.output)
        print(f"Excel report generated at: {path}")
    else:
        print("No action specified. Use --demo to generate a report.")
        sys.exit(0)
