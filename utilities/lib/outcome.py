#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


import enum


class Outcome(enum.StrEnum):
    PASS = "PASS"  # A test must pass, or the adapter signals a passed test
    FAIL = "FAIL"  # A test must fail, or the adapter signals a failed test
    ERROR = "ERROR"  # There was a error running the test adapter or parsing its result.
