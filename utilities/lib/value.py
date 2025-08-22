#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


import math


class Value:
    # Default tolerances and threshold for special float handling
    DEFAULT_REL_TOL = 1e-9
    DEFAULT_ABS_TOL = 1e-10
    LARGE_THRESHOLD = 1e307

    def __init__(self, value_type: str, value: str):
        self.type = value_type
        self.value = value

    def __str__(self):
        """Display the object contexts for debugging purposes."""
        return f"Value(type={self.type}, value={self.value})"

    def to_outcome_text(self):
        return f"{self.type}({self.value})"

    def compare_with_expected(self, expected_value: "Value") -> str:
        if self.type != expected_value.type:
            return f"Expected type {expected_value.type}, got {self.type}"
        if self.type != "Float":
            if self.value != expected_value.value:
                return f"Expected value {expected_value.value}, got {self.value}"
        else:
            return self._compare_float(expected_value)
        return ""  # perfect match

    def _compare_float(self, expected_value) -> str:
        try:
            a = float(self.value)
            b = float(expected_value.value)
        except ValueError:
            return f"Expected value {expected_value.value}, got {self.value}"
        # Handle NaNs explicitly: NaN never equals anything (including NaN)
        if math.isnan(b):
            if not math.isnan(a):
                return f"Expected value {expected_value.value}, got {self.value}"
            else:
                return ""  # matches
        # Accept inf/-inf with large finite values (> 1e+307) of same sign
        # If one is infinite and the other is a large finite with matching sign, accept
        if math.isinf(a) and not math.isinf(b):
            if (b > self.LARGE_THRESHOLD and a > 0) or (b < -self.LARGE_THRESHOLD and a < 0):
                return ""  # treat as acceptable match
            return f"Expected value {expected_value.value}, got {self.value}"
        if math.isinf(b) and not math.isinf(a):
            if (a > self.LARGE_THRESHOLD and b > 0) or (a < -self.LARGE_THRESHOLD and b < 0):
                return ""  # treat as acceptable match
            return f"Expected value {expected_value.value}, got {self.value}"
        # If both infinite, require same sign
        if math.isinf(a) and math.isinf(b):
            if (a > 0 and b > 0) or (a < 0 and b < 0):
                return ""
            return f"Expected value {expected_value.value}, got {self.value}"
        # Relative/absolute tolerance check
        diff = abs(a - b)
        max_ab = max(abs(a), abs(b))
        rel_tol = self.DEFAULT_REL_TOL
        abs_tol = self.DEFAULT_ABS_TOL
        # Accept if within either relative or absolute tolerance
        if diff <= max(rel_tol * max_ab, abs_tol):
            return ""
        else:
            return f"Expected value {expected_value.value}, got {self.value}"
