#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0

"""
MAINTENANCE TOOL - ONLY USED FOR DEVELOPMENT

This script uses a reference implementation to update and verify existing outcome files of the test suite.
It uses the reference implementation to check and update the outcome files for the test files.

Please read the documentation about this test suite. It contains details about the numbering scheme used for the
test files, the directory structure, and file formats.
"""

import argparse
import datetime
import sys
import time
from pathlib import Path
from typing import Optional

from utilities.lib.adapter_runner import AdapterRunner
from utilities.lib.error import Error
from utilities.lib.outcome_parser import parse_outcome
from utilities.lib.outcome_data import OutcomeData
from utilities.lib.comparison_result import ComparisonResult
from utilities.lib.comparison_status import ComparisonStatus


class TestFileSet:
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.outcome_file = config_file.with_suffix(".out")


class WorkingSet:

    def __init__(self):
        self.utilities_path = Path(__file__).parent
        self.project_path = self.utilities_path.parent
        self.tests_path = self.project_path / "tests" / "V1_0"
        self.adapter: Optional[AdapterRunner] = None
        self.test_file_sets: list[TestFileSet] = []
        self.verbose = False
        self.silent = False

    def run(self):
        self.parse_arguments()
        self.adapter.selftest()
        self.scan_outcome_files()
        self.process_test_cases()
        print(">>> SUCCESS")

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Update and verify outcome files of the test suite.")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
        parser.add_argument("-s", "--silent", action="store_true", help="Disable all output.")
        parser.add_argument("testadapter", type=Path, help="Path to the test adapter executable.")
        args = parser.parse_args()
        self.adapter = AdapterRunner(args.testadapter)
        self.verbose = args.verbose
        self.silent = args.silent
        if self.silent:
            self.verbose = False

    def scan_outcome_files(self):
        if self.verbose:
            print("Scanning all test files...")
        test_file_count = 0
        outcome_file_count = 0
        for path in self.tests_path.rglob("*.elcl"):
            test_file_set = TestFileSet(path)
            self.test_file_sets.append(test_file_set)
            test_file_count += 1
            if test_file_set.outcome_file.is_file():
                outcome_file_count += 1
        if not self.test_file_sets:
            raise Error("No test files found.")
        self.test_file_sets.sort(key=lambda x: x.config_file)
        outcome_percentage = outcome_file_count / test_file_count * 100
        if self.verbose:
            print(f"Found {test_file_count} test files with {outcome_percentage:.1f}% outcome files.")

    def process_test_cases(self):
        if self.verbose:
            print("Processing test cases...")
        next_progress_report = time.time() + 5.0
        for index, test_file_set in enumerate(self.test_file_sets):
            if not self.silent and time.time() > next_progress_report:
                progress = index / len(self.test_file_sets) * 100
                print(f"  Progress: {index+1}/{len(self.test_file_sets)} ({progress:.1f}%)")
                next_progress_report = time.time() + 5.0
            if self.verbose:
                print("Processing test file: " + str(test_file_set.config_file.relative_to(self.tests_path)))
            self.process_test_file_set(test_file_set)

    def process_test_file_set(self, test_file_set: TestFileSet):
        expected_outcome: Optional[OutcomeData] = None
        if test_file_set.outcome_file.is_file():
            if self.verbose:
                print("  Reading outcome file...")
            expected_outcome = parse_outcome(test_file_set.outcome_file)
        else:
            if self.verbose:
                print("  No outcome file found.")
        if self.verbose:
            print("  Running the test adapter and parsing its output...")
        actual_outcome = self.adapter.run(test_file_set.config_file)
        if not expected_outcome:
            if self.verbose:
                print("  No expected outcome file found. Creating a new one.")
            actual_outcome.write(test_file_set.outcome_file)
            return
        comparison_result = actual_outcome.compare_with_expected(expected_outcome)
        self._display_comparison_result(
            str(test_file_set.config_file.relative_to(self.tests_path)), actual_outcome, comparison_result
        )

    def _display_comparison_result(
        self, test_file: str, actual_outcome: OutcomeData, comparison_result: ComparisonResult
    ):
        if comparison_result.status == ComparisonStatus.PASS:
            if self.verbose:
                print("  Outcome file matches the expected outcome.")
            return
        elif comparison_result.status == ComparisonStatus.PASS_WITH_ACCEPTED_DEVIATION:
            print(f"Deviation: {test_file}")
            self._display_differences(comparison_result)
        else:
            print(f"Failed: {test_file}")
            self._display_differences(comparison_result)
            if actual_outcome.error_message:
                print(f"  Error message: {actual_outcome.error_message}")

    def _display_differences(self, comparison_result: ComparisonResult):
        for difference_line in comparison_result.differences[:10]:
            print(f"  {difference_line}")
        if len(comparison_result.differences) > 10:
            print(f"  ... +{len(comparison_result.differences)-10} more differences")


if __name__ == "__main__":
    ws = WorkingSet()
    try:
        ws.run()
        exit(0)
    except Error:
        exit(1)
