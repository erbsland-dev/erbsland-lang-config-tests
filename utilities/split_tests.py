#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0

"""
MAINTENANCE TOOL - ONLY USED FOR DEVELOPMENT

This script splits a single test file into many small test files. The names for the test files are placed in
comments, *either* after the values or between line groups.

```
[main]
value: 123  # test name 1
value: 12   # test name 2
value: 1    # test name 3
```

... or ...

```
[main]
# test name 1
value:
    123
# test name 2
value:
    456
```

The script automatically detects the file mode based on the position of the first found comment. The comments with
the names are removed from the tests.
"""

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Tuple, Optional


class ScriptError(Exception):
    pass


class WorkingSet:
    RE_FILE_NUMBER = re.compile(r"^(\d{4})-.*\.elcl$", re.I)
    RE_COMMENT = re.compile(r"#\s*([a-z0-9 ]+)$", re.I)

    def __init__(self):
        self.template_path = Path()
        self.destination_dir = Path()
        self.header_count: int = 0
        self.test_type: str = ""
        self.multi_line_mode: Optional[bool] = None
        self.header_lines: list[str] = []
        self.sequence: int = 0
        self.increment: int = 5

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Generate individual test files from a template.")
        parser.add_argument("template_path", type=Path, help="Path to the template file.")
        parser.add_argument(
            "destination_dir", type=Path, nargs="?", help="Destination directory for the generated test files."
        )
        parser.add_argument(
            "-l",
            "--lines",
            type=int,
            default=2,
            help="Number of header lines to include in each test file (default: 2).",
        )
        parser.add_argument("-t", "--type", type=str, default="PASS", help="The test mode, PASS or FAIL.")
        args = parser.parse_args()
        self.template_path = args.template_path
        self.destination_dir = args.destination_dir
        self.header_count = args.lines
        self.test_type = args.type.upper()
        # Ensure destination directory exists
        if not self.template_path.is_file():
            raise ScriptError("The template file does not exist.")
        if not self.destination_dir:
            self.destination_dir = self.template_path.parent
        if self.header_count < 0 or self.header_count > 10:
            raise ScriptError("The number of header lines must be between 0 and 10.")
        if self.test_type not in ["PASS", "FAIL"]:
            raise ScriptError("The mode must be PASS or FAIL")

    def read_template(self) -> list[str]:
        with self.template_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line.rstrip("\n") for line in lines]

    def split_template(self, lines: list[str]) -> Tuple[list[str], list[str]]:
        if self.header_count > len(lines):
            sys.exit(f"Error: Header line count ({self.header_count}) exceeds total lines in template.")
        headers = lines[: self.header_count]
        test_lines = lines[self.header_count :]
        return headers, test_lines

    def get_existing_sequence_numbers(self) -> list[int]:
        existing_numbers: list[int] = []
        for file in self.destination_dir.iterdir():
            if file.is_file():
                match = self.RE_FILE_NUMBER.match(file.name)
                if match:
                    existing_numbers.append(int(match.group(1)))
        return existing_numbers

    def extract_name(self, test_line: str) -> str:
        """Match the comment starting with # followed by lowercase letters, numbers, and spaces"""
        match = self.RE_COMMENT.search(test_line)
        if not match:
            if self.multi_line_mode is True:
                return ""  # Indicate a line without name.
            raise ScriptError(f"Error: Test line '{test_line}' does not contain a valid comment.")
        if self.multi_line_mode is None:
            self.multi_line_mode = match.start() == 0
        if self.multi_line_mode is True and match.start() != 0:
            return ""
        name = match.group(1).strip().lower().replace(" ", "_")
        return name

    def remove_comment(self, test_line: str) -> str:
        """Remove the comment part"""
        return self.RE_COMMENT.sub("", test_line).rstrip()

    def split_test_lines(self, test_lines: list[str]):
        collected_lines: list[str] = []
        last_name = ""
        for line in test_lines:
            name = self.extract_name(line)
            if not name:
                collected_lines.append(line)
                continue
            if self.multi_line_mode:
                if last_name and collected_lines:
                    self.write_test(last_name, collected_lines)
                collected_lines = self.header_lines.copy()
                last_name = name
                continue
            self.write_test(name, self.header_lines + [self.remove_comment(line)])
        if self.multi_line_mode and last_name and collected_lines:
            self.write_test(last_name, collected_lines)

    def write_test(self, name: str, test_content: list[str]):
        filename = f"{self.sequence:04d}-{self.test_type}-{name}.elcl"
        file_path = self.destination_dir / filename
        with file_path.open("w", encoding="utf-8") as f:
            for content_line in test_content:
                f.write(content_line + "\n")
        print(f"Created: {file_path.name}")
        self.sequence += self.increment

    def main(self):
        self.parse_arguments()

        # Read and split the template
        template_lines = self.read_template()
        headers, test_lines = self.split_template(template_lines)

        if not test_lines:
            raise ScriptError("Error: No test lines found in the template after the header.")
        self.header_lines = headers

        # Determine the starting sequence number
        existing_sequences = self.get_existing_sequence_numbers()
        if existing_sequences:
            max_existing = max(existing_sequences)
            max_existing = int((max_existing // 5) * 5)  # Round to 5 increments
            self.sequence = max_existing + 5
        else:
            self.sequence = 0

        # Check if the starting sequence exceeds 9999
        if self.sequence > 9999:
            raise ScriptError("Error: Sequence number exceeds 9999.")

        # Generate the test files
        self.split_test_lines(test_lines)


if __name__ == "__main__":
    try:
        ws = WorkingSet()
        ws.main()
    except ScriptError as e:
        exit(str(e))
