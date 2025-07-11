#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0


import enum
from functools import cache


class ErrorClass(enum.StrEnum):
    IO = "IO"
    Encoding = "Encoding"
    UnexpectedEnd = "UnexpectedEnd"
    Character = "Character"
    Syntax = "Syntax"
    LimitExceeded = "LimitExceeded"
    NameConflict = "NameConflict"
    Indentation = "Indentation"
    Unsupported = "Unsupported"
    Signature = "Signature"
    Access = "Access"
    Validation = "Validation"
    Internal = "Internal"


@cache
def error_class_str_map() -> dict[str, ErrorClass]:
    result = dict()
    for error_class in ErrorClass:
        result[str(error_class).lower()] = ErrorClass(error_class)
    return result


def parse_error_class(error_class: str) -> ErrorClass:
    return error_class_str_map()[error_class.lower()]
