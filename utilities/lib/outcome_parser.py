#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


import re
from pathlib import Path

from utilities.lib.error import Error
from utilities.lib.error_class import parse_error_class
from utilities.lib.outcome import Outcome
from utilities.lib.outcome_data import OutcomeData
from utilities.lib.value import Value


RE_VALUE_LINE = re.compile(r"^([^=]+)\s*=\s*(\w+)\((.*)\)\s*$", re.I)
RE_FAIL_LINE = re.compile(r"^FAIL\s*=\s*(.*)\s*$", re.I)
RE_FAIL_ERROR = re.compile(r"^(\w+)(?:\((.*)\))?$")


def parse_outcome(path: Path) -> OutcomeData:
    text = path.read_text(encoding="utf-8")
    if "PASS" in path.name:
        return parse_pass(text)
    elif "FAIL" in path.name:
        return parse_fail(text)
    else:
        raise Error(f"Error: Unknown outcome file name: {path.name}")


def parse_pass(text: str) -> OutcomeData:
    """
    Parse the outcome of a PASS test.
    """
    result = OutcomeData(Outcome.PASS)
    line_count = 1
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            line_count += 1
            continue  # skip empty line or lines with comments.
        match = RE_VALUE_LINE.match(line)
        if not match:
            raise Error(f"Error in line {line_count}: Unexpected format for value")
        value = Value(match.group(2).strip(), match.group(3).strip())
        if match.group(1) in result.values:
            raise Error(f"Error in line {line_count}: Duplicated name-path: {match.group(1)}")
        result.values[match.group(1).strip()] = value
        line_count += 1
    return result


def parse_fail(text: str) -> OutcomeData:
    result = OutcomeData(Outcome.FAIL)
    line_count = 1
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            line_count += 1
            continue  # skip empty line or lines with comments.
        if result.error_classes:
            raise Error(f"Error in line {line_count}: Error classes already defined in previous lines")
        match = RE_FAIL_LINE.match(line)
        if not match:
            raise Error(f"Error in line {line_count}: Unexpected format for failure line")
        error_classes = match.group(1).split("|")
        for error_class in error_classes:
            error_class = error_class.strip()
            if not error_class:
                continue
            match = RE_FAIL_ERROR.match(error_class)
            if not match:
                raise Error(f"Error in line {line_count}: Invalid error class format: {error_class}")
            try:
                error_class = parse_error_class(match.group(1))
            except ValueError:
                raise Error(f"Error in line {line_count}: Unknown error class: {error_class}")
            if error_class in result.error_classes:
                raise Error(f"Error in line {line_count}: Duplicated error class: {error_class}")
            result.error_classes.append(error_class)
            if match.group(2):
                result.error_message = match.group(2)
    return result
