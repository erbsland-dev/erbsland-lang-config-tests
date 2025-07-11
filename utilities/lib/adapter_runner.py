#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from utilities.lib.error import Error
from utilities.lib.outcome import Outcome
from utilities.lib.outcome_parser import parse_pass, parse_fail
from utilities.lib.outcome_data import OutcomeData


class AdapterRunnerError(Error):
    pass


class AdapterRunner:
    """
    A class to run the test adapter and parse its output.
    """

    def __init__(self, testadapter_path: Path):
        self.testadapter = Path(testadapter_path)
        self.testadapter = testadapter_path.resolve()
        if not self.testadapter.is_file():
            raise AdapterRunnerError(f"Couldn't find the test adapter executable at this path: {self.testadapter}")

    def selftest(self):
        """
        Start the test adapter with a test file to verify it's functionality.
        """
        result: Optional[OutcomeData] = None
        with tempfile.NamedTemporaryFile("wt", delete_on_close=False) as test_file:
            test_file.write("[main]\nvalue: 123\n")
            test_file.close()
            test_file_path = Path(test_file.name)
            result = self.run(test_file_path)
        if result.status != Outcome.PASS:
            raise AdapterRunnerError(f"Test adapter failed the sanity test. Returned FAIL on valid test file.")
        # Do not test the values

    def run(self, test_file: Path) -> OutcomeData:
        """
        Run the test adapter with the given test file and capture its output.

        :param test_file: Path to the test file to process.
        :returns: The captured standard output from the test adapter.
        """
        args = [str(self.testadapter), "--version", "1.0", str(test_file)]
        result: Optional[subprocess.CompletedProcess] = None
        try:
            try:
                result = subprocess.run(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=10.0,
                )
            except subprocess.TimeoutExpired:
                raise AdapterRunnerError("Test adapter timed out after 10 seconds.")
            if result.returncode == 0:
                return parse_pass(result.stdout)
            elif result.returncode == 1:
                outcome_result = parse_fail(result.stdout)
                if len(outcome_result.error_classes) != 1:
                    raise AdapterRunnerError(
                        f"Test adapter returned {len(outcome_result.error_classes)} error classes, instead of one."
                    )
                return outcome_result
            else:
                raise AdapterRunnerError(f"Test adapter returned unexpected exit code: {result.returncode}")
        except Error as e:
            print(">>> ERROR while running the test adapter: ", e)
            print("Command: " + " ".join(args))
            print("Output:")
            print(result.stdout)
            print(result.stderr)
            raise
