#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


import enum


class ComparisonStatus(enum.StrEnum):
    PASS = "pass"
    PASS_WITH_ACCEPTED_DEVIATION = "pass_with_accepted_deviation"
    FAIL = "fail"
