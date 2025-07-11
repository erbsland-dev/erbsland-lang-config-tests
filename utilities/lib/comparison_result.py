#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


from utilities.lib.comparison_status import ComparisonStatus


class ComparisonResult:
    def __init__(self):
        self.status = ComparisonStatus.PASS
        self.differences: list[str] = []
        self.score = 0
