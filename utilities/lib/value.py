#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


class Value:
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
            try:
                if abs(float(self.value) - float(expected_value.value)) > 0.000001:
                    return f"Expected value {expected_value.value}, got {self.value}"
            except ValueError:
                return f"Expected value {expected_value.value}, got {self.value}"
        return ""  # perfect match
