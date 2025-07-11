#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0

"""
Conformance Test for Erbsland Configuration Language

This script tests a parser against all test cases in this test suite. It requires a test adapter that
outputs the parsing result in a special format.

Please read the documentation about this test suite for more details:
https://github.com/erbsland-dev/erbsland-lang-config-doc
"""
import argparse
import enum
import json
import sys
from pathlib import Path
from typing import Optional
import multiprocessing
from multiprocessing import Pool

from utilities.lib.adapter_runner import AdapterRunner
from utilities.lib.comparison_result import ComparisonResult
from utilities.lib.comparison_status import ComparisonStatus
from utilities.lib.error import Error
from utilities.lib.outcome_parser import parse_outcome


class OutputFormat(enum.StrEnum):
    TEXT = "text"
    JSON = "json"


class ParserTier(enum.StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class TestCase:
    def __init__(self, identifier: int, test_path: Path):
        self.identifier = identifier
        self.test_path = test_path
        self.outcome_path = test_path.with_suffix(".out")
        self.result: Optional[ComparisonResult] = None


TIERS = {
    ParserTier.MINIMAL: [
        "byte-count",
        "core",
        "float",
    ],
    ParserTier.STANDARD: [
        "byte-count",
        "byte-data",
        "code",
        "core",
        "date-time",
        "float",
        "multiline-byte-data",
        "multiline-code",
        "multiline-text",
        "section-list",
        "text-names",
        "value-list",
    ],
    ParserTier.FULL: [
        "byte-count",
        "byte-data",
        "code",
        "core",
        "date-time",
        "float",
        "multiline-byte-data",
        "multiline-code",
        "multiline-regex",
        "multiline-text",
        "regex",
        "section-list",
        "text-names",
        "time-delta",
        "value-list",
    ],
}


class WorkingSet:

    def __init__(self):
        self.project_path = Path(__file__).parent
        self.tests_path = self.project_path / "tests" / "V1_0"
        self.adapter: Optional[AdapterRunner] = None

        self.output = sys.stdout
        self.silent = False
        self.tier = ParserTier.FULL
        self.format = OutputFormat.TEXT

        self.test_cases: list[TestCase] = []
        self.test_casse_map: dict[int, TestCase] = {}
        self.result = ComparisonStatus.PASS
        self.passed_test_count = 0
        self.passed_with_deviation_test_count = 0
        self.failed_test_count = 0
        self.score = 0

    def run(self):
        try:
            self.parse_arguments()
            self.banner()
            self.scan_test_cases()
            self.run_tests()
            self.output_results()
            if self.result == ComparisonStatus.FAIL:
                exit(1)
            exit(0)
        except Error as e:
            print(f"ERROR: {e}")
            exit(2)

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Test the conformance of a configuration parser.")
        parser.add_argument("-s", "--silent", action="store_true", help="Disable all progress output.")
        parser.add_argument(
            "-f",
            "--format",
            type=OutputFormat,
            default=OutputFormat.TEXT,
            help="Output format. Either 'text' or 'json'. Default is 'text'.",
        )
        parser.add_argument("-o", "--output", type=Path, help="Write all output to this path.")
        parser.add_argument(
            "-t",
            "--tier",
            type=ParserTier,
            default=ParserTier.FULL,
            help="Select the parser tier. Select 'minimal', 'standard', or 'full'. Default is 'full'.",
        )
        parser.add_argument(
            "-l",
            "--lang-version",
            type=str,
            default="1.0",
            help="Select the language version to test. The default and currently the only possible version is '1.0'.",
        )
        parser.add_argument("testadapter", type=Path, help="Path to the test adapter executable.")
        args = parser.parse_args()
        self.adapter = AdapterRunner(args.testadapter)
        self.format = OutputFormat(args.format)
        self.tier = ParserTier(args.tier)
        self.silent = args.silent
        if args.lang_version != "1.0":
            raise Error(f"Unsupported language version: {args.lang_version}")
        if args.output:
            self.output = open(args.output, "wt")

    def banner(self):
        if not self.silent:
            print("Erbsland Configuration Language - Conformance Test")
            print("-" * 78)

    def scan_test_cases(self):
        if not self.silent:
            print(f"Scanning all test cases for tier '{self.tier.value}'...")
        included_sub_directories = TIERS[self.tier]
        test_case_count = 0
        for path in self.tests_path.rglob("*.elcl"):
            rel_path = path.relative_to(self.tests_path)
            if rel_path.parts[0] not in included_sub_directories:
                continue
            test_case = TestCase(test_case_count, path)
            self.test_cases.append(test_case)
            self.test_casse_map[test_case.identifier] = test_case
            if not test_case.outcome_path.is_file():
                raise Error(
                    f"The outcome file for a test case is missing: {test_case.outcome_path.relative_to(self.tests_path)}"
                )
            test_case_count += 1
        if not self.test_cases:
            raise Error("No test files found.")
        self.test_cases.sort(key=lambda x: x.test_path)

    @staticmethod
    def _process_test_case(args: tuple[TestCase, AdapterRunner]) -> tuple[TestCase, ComparisonResult]:
        test_case, adapter = args
        try:
            result = adapter.run(test_case.test_path)
            expected = parse_outcome(test_case.outcome_path)
            return test_case, result.compare_with_expected(expected)
        except Error as e:
            result = ComparisonResult()
            result.status = ComparisonStatus.FAIL
            result.differences.append(f": {e}")
            return test_case, result

    def run_tests(self):
        if not self.silent:
            print(f"Running all tests...")
        num_processes = max(4, multiprocessing.cpu_count() - 1)
        with Pool(processes=num_processes) as pool:
            args = [(tc, self.adapter) for tc in self.test_cases]
            results = pool.map(self._process_test_case, args)
        for returned_test_case, result in results:
            # Store the result in the local test case object.
            self.test_casse_map[returned_test_case.identifier].result = result
            if result.status == ComparisonStatus.FAIL:
                self.result = ComparisonStatus.FAIL
                self.failed_test_count += 1
            elif result.status == ComparisonStatus.PASS_WITH_ACCEPTED_DEVIATION:
                self.passed_with_deviation_test_count += 1
            else:
                self.passed_test_count += 1
            self.score += result.score

    def output_results(self):
        if self.format == OutputFormat.TEXT:
            self.output_text()
        elif self.format == OutputFormat.JSON:
            self.output_json()
        else:
            raise Error(f"Unknown output format: {self.format}")
        if self.output != sys.stdout:
            self.output.close()

    def output_text(self):
        self.output.write("-*" + "=" * 74 + "*-\n\n")
        if self.result == ComparisonStatus.PASS:
            self.output.write(" " * 20 + "+*+    Conformance test PASSED    +*+\n\n")
        else:
            self.output.write(" " * 20 + "XXX    Conformance test FAILED    XXX\n\n")
        total_test_count = len(self.test_cases)
        pass_percentage = self.passed_test_count / total_test_count * 100
        self.output.write(f"    {pass_percentage:.2f}% tests passed ({self.passed_test_count}/{total_test_count})\n")
        if self.passed_with_deviation_test_count > 0:
            pass_with_deviation_percentage = self.passed_with_deviation_test_count / total_test_count * 100
            self.output.write(
                f"    {pass_with_deviation_percentage:.2f}% tests passed with acceptable deviation ({self.passed_with_deviation_test_count}/{total_test_count})\n"
            )
        if self.failed_test_count > 0:
            fail_percentage = self.failed_test_count / total_test_count * 100
            self.output.write(
                f"    {fail_percentage:.2f}% tests failed ({self.failed_test_count}/{total_test_count})\n"
            )
        self.output.write("\n")
        self.output.write(f"    {self.tier.title()}-Tier Parser Score: {self.score}\n\n")
        self.output.write("-*" + "=" * 74 + "*-\n\n")
        if self.failed_test_count > 0:
            self.output.write(f"{self.failed_test_count} Failed Tests:\n\n")
            self._output_text_details(ComparisonStatus.FAIL)
        if self.passed_with_deviation_test_count > 0:
            self.output.write(f"{self.passed_with_deviation_test_count} Passed Tests with Acceptable Deviation:\n\n")
            self._output_text_details(ComparisonStatus.PASS_WITH_ACCEPTED_DEVIATION)

    def _output_text_details(self, status: ComparisonStatus):
        limit_count = 0
        test_cases = list([t for t in self.test_cases if t.result.status == status])
        for test_case in test_cases:
            self.output.write(f"  Test {test_case.test_path.relative_to(self.tests_path)}:\n")
            for difference_line in test_case.result.differences:
                self.output.write(f"    - {difference_line}\n")
            limit_count += 1
            if limit_count >= 10:
                self.output.write(f"  ... +{len(test_cases)-limit_count} more\n")
                break

    def output_json(self):
        result = {
            "result": self.result.value,
            "total_test_count": len(self.test_cases),
            "passed_test_count": self.passed_test_count,
            "passed_with_deviation_test_count": self.passed_with_deviation_test_count,
            "failed_test_count": self.failed_test_count,
            "score": self.score,
            "tier": self.tier.value,
            "differences": [],
        }
        test_cases = list([t for t in self.test_cases if t.result.status != ComparisonStatus.PASS])
        tests = []
        for test_case in test_cases:
            test = {
                "status": test_case.result.status.value,
                "test_path": str(test_case.test_path.relative_to(self.tests_path)),
                "differences": test_case.result.differences,
            }
            tests.append(test)
        result["differences"] = tests
        self.output.write(json.dumps(result, indent=2))


if __name__ == "__main__":
    ws = WorkingSet()
    ws.run()
