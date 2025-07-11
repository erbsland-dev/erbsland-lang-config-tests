#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from utilities.lib.comparison_result import ComparisonResult
from utilities.lib.comparison_status import ComparisonStatus
from utilities.lib.error_class import ErrorClass
from utilities.lib.outcome import Outcome
from utilities.lib.value import Value


class OutcomeData:

    ACCEPTED_SYNTAX_ERRORS = [
        ErrorClass.UnexpectedEnd,
        ErrorClass.Character,
        ErrorClass.LimitExceeded,
        ErrorClass.Indentation,
        ErrorClass.Unsupported,
    ]

    def __init__(self, status: Outcome):
        self.status: Outcome = status
        self.error_classes: list[ErrorClass] = []
        self.error_message: str = ""
        self.values: dict[str, Value] = {}

    def __str__(self):
        """Display the object contexts for debugging purposes."""
        values = "\n".join(f"    {n} = {v}" for n, v in self.values.items())
        return (
            f"OutcomeResult:\n  status={self.status}\n  error_classes={', '.join(self.error_classes)}\n"
            + f"  values:\n{values})"
        )

    def write(self, outcome_file: Path):
        """Write the outcome result to a file."""
        with outcome_file.open("wt", encoding="utf-8") as f:
            if self.status == Outcome.PASS:
                for name_path in sorted(self.values.keys()):
                    value = self.values[name_path]
                    f.write(f"{name_path} = {value.to_outcome_text()}\n")
            else:
                f.write(f"FAIL = {'|'.join(self.error_classes)}\n")

    def compare_with_expected(self, expected: "OutcomeData") -> ComparisonResult:
        """Compare the outcome result with the expected outcome result."""
        result = ComparisonResult()
        if self.status != expected.status:
            result.status = ComparisonStatus.FAIL
            result.differences.append(f"Status: expected {expected.status}, got {self.status}")
            return result
        if self.status == Outcome.FAIL:
            if len(self.error_classes) != 1:
                raise ValueError(f"Error classes: expected one, got {len(self.error_classes)}")
            actual_error_class = self.error_classes[0]
            if actual_error_class not in expected.error_classes:
                if actual_error_class == ErrorClass.Syntax and expected.error_classes[0] in self.ACCEPTED_SYNTAX_ERRORS:
                    result.status = ComparisonStatus.PASS_WITH_ACCEPTED_DEVIATION
                    result.differences.append(
                        f"Expected error {expected.error_classes[0]} but got {self.error_classes[0]}, which is also accepted."
                    )
                    result.score = 8
                else:
                    result.status = ComparisonStatus.FAIL
                    result.differences.append(
                        f"Error classes: expected one of {', '.join(expected.error_classes)}, got {self.error_classes[0]}"
                    )
            else:
                result.status = ComparisonStatus.PASS
                result.score = 10
            return result
        ignored_meta_names = ["@version", "@features"]
        actual_name_paths = [n.lower() for n in sorted(self.values.keys()) if n not in ignored_meta_names]
        expected_name_paths = [n.lower() for n in sorted(expected.values.keys()) if n not in ignored_meta_names]
        for name_path in actual_name_paths:
            if name_path not in expected_name_paths:
                result.status = ComparisonStatus.FAIL
                result.differences.append(f"Name path: Unexpected name-path '{name_path}'")
        for name_path in expected_name_paths:
            if name_path not in actual_name_paths:
                result.status = ComparisonStatus.FAIL
                result.differences.append(f"Name path: Missing name-path '{name_path}'")
        if result.status == ComparisonStatus.FAIL:
            return result
        for name_path in sorted(self.values.keys()):
            if name_path in ignored_meta_names:
                continue
            actual_value = self.values[name_path]
            expected_value = expected.values[name_path]
            value_result = actual_value.compare_with_expected(expected_value)
            if value_result:
                result.status = ComparisonStatus.FAIL
                result.differences.append(f"Value '{name_path}' does not match: {value_result}")
        result.score = 10
        return result
