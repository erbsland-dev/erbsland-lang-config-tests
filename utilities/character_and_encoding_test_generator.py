#  Copyright (c) 2025. Erbsland DEV. https://erbsland.dev
#  SPDX-License-Identifier: Apache-2.0

"""
MAINTENANCE TOOL - ONLY USED FOR DEVELOPMENT

This script generates technical test files based on templates to cover a wide range of test cases.
These files test encoding errors, unexpected control codes, unexpected ends, unexpected but valid characters,
missing characters, and invalid character ranges.

Please read the documentation about this test suite. It contains details about the numbering scheme used for the
test files, the directory structure, and file formats.
"""

import enum
import itertools
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from utilities.lib.error_class import ErrorClass
from utilities.lib.outcome import Outcome


class Category(enum.StrEnum):
    EMPTY = "01_empty"  # Empty documents
    ENCODING = "02_encoding"  # Encoding errors at various locations.
    CONTROL = "03_control"  # Control codes at various locations.
    UNEXPECTED_END = "04_unexpected_end"  # Unexpected end of document.
    INSERTS = "05_inserts"  # Inserted valid characters at the wrong places
    DELETIONS = "06_deletions"  # Deleted characters.
    RANGES = "07_ranges"  # Testing character ranges


@dataclass
class RangeInsert:
    text: str  # The inserted text.
    name: str  # A name for the filename.
    outcome: Outcome  # The expected outcome.


class TestFile:
    """The definition of a single test file."""

    def __init__(
        self,
        name: str,
        outcome: Outcome,
        *,
        error: ErrorClass | list[ErrorClass] = ErrorClass.Encoding,
        add_bom: bool = False,
        template: str = None,
        content: bytes = None,
        subdir: str = None,
        feature: str = "core",
        output: str = None,
    ):
        self.name = name
        self.outcome = outcome
        self.error = error
        self.add_bom = add_bom
        self.template = template
        self.content = content
        self.subdir = subdir
        self.feature = feature
        self.output = output


class WorkingSet:

    SPACING = [("sp", b" "), ("t", b"\t"), ("nl", b"\n"), ("crlf", b"\r\n")]
    INVALID_CONTROL = [*range(0x00, 0x09), 0x0B, *range(0x0E, 0x20), *range(0x7F, 0xA0)]
    INVALID_UTF8_SEQUENCES = [
        # Surrogate code points (U+D800–U+DFFF)
        b"\xed\xa0\x80",  # U+D800 high surrogate
        b"\xed\xa0\x81",  # U+D801 high surrogate
        b"\xed\xad\xbf",  # U+DB7F high surrogate
        b"\xed\xae\x80",  # U+DB80 high surrogate
        b"\xed\xaf\xbf",  # U+DBFF high surrogate
        b"\xed\xb0\x80",  # U+DC00 low surrogate
        b"\xed\xb0\x81",  # U+DC01 low surrogate
        b"\xed\xbe\x80",  # U+DF80 low surrogate
        b"\xed\xbf\xbf",  # U+DFFF low surrogate
        b"\xed\xaf\xc0",  # Invalid continuation in surrogate range
        # Code points outside the valid Unicode range (U+110000–U+FFFFFFFF)
        b"\xf4\x90\x80\x80",  # U+110000
        b"\xf5\x80\x80\x80",  # Above U+10FFFF
        b"\xf6\x80\x80\x80",  # Above U+10FFFF
        b"\xf7\x80\x80\x80",  # Above U+10FFFF
        b"\xf8\x88\x80\x80\x80",  # 5-byte sequence (invalid in UTF-8)
        b"\xf9\x80\x80\x80\x80",  # 5-byte sequence (invalid in UTF-8)
        b"\xfa\x80\x80\x80\x80",  # 5-byte sequence (invalid in UTF-8)
        b"\xfb\x80\x80\x80\x80",  # 5-byte sequence (invalid in UTF-8)
        b"\xfc\x84\x80\x80\x80\x80",  # 6-byte sequence (invalid in UTF-8)
        b"\xfd\x80\x80\x80\x80\x80",  # 6-byte sequence (invalid in UTF-8)
        # Other invalid UTF-8 byte sequences
        b"\xc0",  # Lone start byte (missing continuation byte)
        b"\xe0\x80",  # Incomplete 3-byte sequence
        b"\xf0\x80\x80",  # Incomplete 4-byte sequence
        b"\xc1\xbf",  # Overlong encoding (should be single-byte)
        b"\xe0\x9f\xbf",  # Overlong encoding (should be 2-byte)
        b"\xf0\x8f\xbf\xbf",  # Overlong encoding (should be 3-byte)
        b"\x80",  # Lone continuation byte
        b"\xbf",  # Lone continuation byte
        b"\xfe",  # Invalid start byte
        b"\xff",  # Invalid start byte
    ]
    RANGES = {
        "letter": list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        "digit": list("0123456789"),
        "hex_digit": list("0123456789abcdefABCDEF"),
        "space": list(" "),
        "tab": list("\t"),
        "underscore": list("_"),
        "letter_lookalike": list(
            "ΑΒΕΖΗΙΚΜΝΟΡΤΧΥ"  # U+0391 to U+03A9 (excluding letters that don't resemble Latin letters)
            "αβδεηικμορτυ"  # U+03B1 to U+03C9 Greek small letters that look like Latin letters
            "АВЕЗКМНОРСТХ"  # U+0410 to U+042F Cyrillic capital letters that look like Latin letters
            "аеорсху"  # U+0430 to U+044F Cyrillic small letters that look like Latin letters
            "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"  # Fullwidth Latin letters
            "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
            "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"  # Mathematical Alphanumeric Symbols (bold, italic, etc.)
            "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
            "ᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ"  # Modifier letters that resemble ASCII letters
            "áàâäãåāčçćďđéèêëěīíìîïłńñňóòôöõřšśťúùûüůýžżź"  # Latin letters with diacritics
        ),
        "digit_lookalike": list(
            "０１２３４５６７８９"  # Fullwidth Latin digits
            "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"  # Mathematical Alphanumeric Symbols (bold, italic, etc.)
            "٠١٢٣٤٥٦٧٨٩"  # Arabic-Indic digits
        ),
        "invisible": list("\u200b\u200c\u200d"),  # Zero-width space and other invisible characters
        "combining": [
            "a\u0300",  # 'a' with grave accent
            "e\u0301",  # 'e' with acute accent
            "i\u0302",  # 'i' with circumflex
            "o\u0303",  # 'o' with tilde
            "u\u0308",
        ],
        "escape_letter": list('\\"$tnrTNR'),
        "escape_unicode": [
            "u0009",
            "U222F",
            "u{9}",
            "U{2f}",
            "u{23A}",
            "U{222f}",
            "u{1f923}",
            "U{01f923}",
            "u{001f923}",
            "U{0001f923}",
        ],
        "wrong_escape_letter": list("".join(chr(x) for x in range(0x20, 0x7F) if chr(x) not in '\\"$tnruTNRU')),
        "wrong_escape_unicode": [
            "u0000",  # ELCL does not allow a zero cp in text
            "U0000",
            "u{0}",
            "u{00}",
            "u{000}",
            "u{0000}",
            "u{00000}",
            "u{000000}",
            "u{0000000}",
            "u{00000000}",
            "u{110000}",  # ELCL does only allow valid Unicode cp in text.
            "u{ffffffff}",  # ELCL does only allow valid Unicode cp in text.
        ],
        "escape_lookalike": list("𝐍𝐑𝐒𝐓𝐔𝐧𝐫𝐭𝐮ňřＮＲＴＵТτΤ"),
    }

    RE_INSERT_MAP = re.compile(r"^❮([a-z]):\s*(.*)❯")
    RE_INSERT_TEST = re.compile(r"^❮(fail|pass): *(\w+) *❯")
    RE_INSERT_MARK = re.compile(r"❮([a-z])❯")

    RE_RANGE_MAP = re.compile(r"^❮([a-z]):\s*(.*)❯")
    RE_RANGE_SUBDIR = re.compile(r"^❮subdir: *(\w+) *❯")
    RE_RANGE_TEST = re.compile(r"^❮test: *(\w+) *❯")
    RE_RANGE_MARK = re.compile(r"❮([a-z])❯")

    def __init__(self):
        self.utilities_path = Path(__file__).parent
        self.project_path = self.utilities_path.parent
        self.tests_path = self.project_path / "tests" / "V1_0"
        self.template_path = self.utilities_path / "templates"
        self.test_files: dict[Category, list[TestFile]] = defaultdict(list)

    def initialize_test_files(self):
        """Initialize all test file data."""
        self._initialize_empty()
        self._initialize_valid_spacing()
        self._initialize_all_invalid_utf8()
        self._initialize_range_tests()
        self._initialize_insert_tests()

    def _initialize_empty(self):
        """Empty files and files with only spacing and comments are ok."""
        subdir = "empty"
        self.test_files[Category.ENCODING].extend(
            [
                TestFile("empty", Outcome.PASS, subdir=subdir),
                TestFile("empty_bom", Outcome.PASS, add_bom=True, subdir=subdir),
                TestFile("spacing", Outcome.PASS, template="spacing/comments_and_spacing.elcl", subdir=subdir),
                TestFile(
                    "spacing_bom",
                    Outcome.PASS,
                    template="spacing/comments_and_spacing.elcl",
                    add_bom=True,
                    subdir=subdir,
                ),
            ]
        )

    def _initialize_valid_spacing(self):
        """Create documents with all possible combinations of valid spacing."""
        for length in range(1, 4):
            for combo in itertools.product(self.SPACING, repeat=length):
                content = b"".join(v[1] for v in combo)
                test_name = "_".join(v[0] for v in combo)
                self.test_files[Category.EMPTY].append(TestFile(f"spacing_{test_name}", Outcome.PASS, content=content))

    def _initialize_all_invalid_utf8(self):
        """Test all invalid UTF-8 sequences, start/middle/end of a valid document."""
        subdir = "all_invalid_utf8_sequences"
        for seq in self.INVALID_UTF8_SEQUENCES:
            for template in ["document_start", "value_in_name", "document_end"]:
                template_name = template[3:]
                name = f"utf8_{seq.hex()}_at_{template_name}"
                test_file = TestFile(
                    name,
                    Outcome.FAIL,
                    content=seq,
                    template=f"utf8/{template}.elcl",
                    error=ErrorClass.Encoding,
                    subdir=subdir,
                    feature="core",
                )
                self.test_files[Category.ENCODING].append(test_file)

    def _initialize_insert_tests(self):
        """Tests with inserted encoding errors, and characters."""
        insert_templates = sorted((self.template_path / "inserts").glob("*.elcl"))
        for template_path in insert_templates:
            self._create_insert_tests(template_path)

    def _create_insert_tests(self, template_path: Path):
        """Assuming valid UTF-8 for the template, as the invalid characters get inserted later."""
        header: list[str] = []
        insert_map: dict[str, list[str]] = {}
        test_name: Optional[str] = None
        test_lines: dict[str, list[str]] = defaultdict(list)
        test_type: dict[str, str] = {}
        feature_name: str = template_path.stem
        # Quickly collect everything from the test file.
        with open(template_path, "r", encoding="utf-8") as fp:
            for line in fp.readlines():
                line = line.rstrip("\n\r")
                if match := self.RE_INSERT_MAP.match(line):
                    insert_map[match.group(1)] = match.group(2).split()
                    continue
                if match := self.RE_INSERT_TEST.match(line):
                    test_name = match.group(2).strip()
                    test_type[test_name] = match.group(1)
                    continue
                if not test_name:
                    header.append(line)
                else:
                    test_lines[test_name].append(line)
        for test_name, lines in test_lines.items():
            test_text = "\n".join(header + lines)
            self._generate_insert_tests(test_text, insert_map, test_type[test_name], test_name, feature_name)

    def _generate_insert_tests(
        self, original_text: str, insert_map: dict[str, list[str]], test_type: str, test_name: str, feature_name: str
    ):
        outcome = Outcome.FAIL if test_type == "fail" else Outcome.PASS
        insert_positions: list[Tuple[int, str]] = []
        position = 0
        plain_text = ""
        while match := self.RE_INSERT_MARK.search(original_text, position):
            plain_text += original_text[position : match.start()]
            insert_positions.append((len(plain_text), match.group(1)))
            position = match.end()
        plain_text += original_text[position:]
        invalid_utf8 = itertools.cycle(self.INVALID_UTF8_SEQUENCES)
        invalid_ctrl = itertools.cycle(self.INVALID_CONTROL)
        for position, map_name in insert_positions:
            for insert_name in insert_map[map_name]:
                category, error, insert_data, name = self._prepare_insert_data(
                    insert_name, invalid_ctrl, invalid_utf8, test_name
                )
                if category == Category.DELETIONS:
                    data = plain_text[: position - 1].encode("utf-8")
                else:
                    data = plain_text[:position].encode("utf-8")
                    data += insert_data
                if category != Category.UNEXPECTED_END:
                    data += plain_text[position:].encode("utf-8")
                if category in [Category.ENCODING, Category.CONTROL] and feature_name == "core":
                    subdir = "inserts"
                else:
                    subdir = None
                test_file = TestFile(name, outcome, content=data, error=error, feature=feature_name, subdir=subdir)
                self.test_files[category].append(test_file)

    def _prepare_insert_data(self, insert_name, invalid_ctrl, invalid_utf8, test_name):
        error = ErrorClass.Syntax
        category = Category.INSERTS
        match insert_name:
            case "encoding":
                insert_data = next(invalid_utf8)
                error = ErrorClass.Encoding
                name = f"utf8_{insert_data.hex()}_in_{test_name}"
                category = Category.ENCODING
            case "ctrl":
                insert_data = chr(next(invalid_ctrl)).encode("utf-8")
                error = ErrorClass.Character
                name = f"ctrl_in_{test_name}"
                category = Category.CONTROL
            case "end":
                insert_data = b""
                error = [ErrorClass.UnexpectedEnd, ErrorClass.Syntax]
                category = Category.UNEXPECTED_END
                name = f"end_in_{test_name}"
            case "del":
                insert_data = b""
                category = Category.DELETIONS
                name = f"deletion_in_{test_name}"
            case "space":
                insert_data = b" "
                name = f"space_in_{test_name}"
            case "tab":
                insert_data = b"\t"
                name = f"tab_in_{test_name}"
            case "idel":
                insert_data = b""
                category = Category.DELETIONS
                error = ErrorClass.Indentation
                name = f"deleted_space_{test_name}"
            case "ispace":
                insert_data = b" "
                name = f"extra_space_in_{test_name}"
                error = ErrorClass.Indentation
            case "itab":
                insert_data = b"\t"
                name = f"extra_tab_in_{test_name}"
                error = ErrorClass.Indentation
            case "comma":
                insert_data = b","
                name = f"comma_in_{test_name}"
            case name if name.startswith("0x"):
                insert_data = bytes.fromhex(insert_name[2:])
                name = f"utf8_{insert_data.hex()}_in_{test_name}"
            case _:
                insert_data = insert_name.encode("utf-8")
                if insert_name.isalnum() and insert_name.isascii():
                    name = f"added_{insert_name}_in_{test_name}"
                else:
                    name = f"utf8_{insert_data.hex()}_in_{test_name}"
        return category, error, insert_data, name

    def _initialize_range_tests(self):
        """Testing valid and invalid character ranges at elements in the syntax."""
        range_templates = sorted((self.template_path / "ranges").glob("*.elcl"))
        for range_path in range_templates:
            self._create_range_tests(range_path)

    def _create_range_tests(self, range_path: Path):
        """The template, as the range characters get inserted later."""
        range_token_map: dict[str, list[str]] = {}
        tests: list[Tuple[str, str, list[str]]] = []  # List with (test_name, subdir, lines)
        subdir: Optional[str] = None
        lines: list[str] = []
        header: list[str] = lines  # Initial lines are assigned to the header.
        feature_name: str = range_path.stem
        # Quickly collect everything from the test file.
        with open(range_path, "r", encoding="utf-8") as fp:
            for line in fp.readlines():
                line = line.rstrip("\n\r")
                if match := self.RE_RANGE_MAP.match(line):
                    range_token_map[match.group(1)] = match.group(2).split()
                    continue
                if match := self.RE_RANGE_SUBDIR.match(line):
                    subdir = match.group(1).strip()
                    continue
                if match := self.RE_RANGE_TEST.match(line):
                    test_name = match.group(1).strip()
                    lines = []  # Create a new lines list for the new test.
                    tests.append((test_name, subdir, lines))
                    continue
                lines.append(line)
        # Prepare the ranges from the tokens.
        insert_map: dict[str, list[RangeInsert]] = {}
        for range_name, tokens in range_token_map.items():
            insert_list: list[RangeInsert] = []
            outcome: Optional[Outcome] = None
            for token in tokens:
                if token[0].isupper():
                    if token not in [str(Outcome.PASS), str(Outcome.FAIL)]:
                        raise ValueError(f"Unknown test mode {token}.")
                    outcome = Outcome(token)
                    continue
                if not outcome:
                    raise ValueError(f"Range before mode in range {range_name}")
                if token not in self.RANGES:
                    raise ValueError(f'Unknown character range "{token}" in test {test_name}.')
                for text in self.RANGES[token]:
                    if text.isascii() and text.isalnum():
                        name = f"{token}_{text}"
                    else:
                        name = token
                    insert_list.append(RangeInsert(text=text, name=name, outcome=outcome))
            if not insert_list:
                raise ValueError(f"No tests in range {range_name}")
            insert_map[range_name] = insert_list
        # Generate the tests.
        for test_name, subdir, lines in tests:
            test_text = "\n".join(header + lines)
            self._generate_range_tests(test_text, insert_map, subdir, test_name, feature_name)

    def _generate_range_tests(
        self,
        test_text: str,
        insert_map: dict[str, list[RangeInsert]],
        subdir: str,
        test_name: str,
        feature_name: str,
    ):
        match = self.RE_RANGE_MARK.search(test_text)
        if not match:
            raise ValueError(f"Found no range mark ❮x❯ in test text in test {test_name}.")
        position = match.start()
        selected_range = match.group(1)
        if selected_range not in insert_map:
            raise ValueError(f"Found no range map for mark ❮{selected_range}❯ in test {test_name}.")
        text_front = test_text[:position]
        text_back = test_text[match.end() :]
        if self.RE_RANGE_MARK.search(text_back):
            raise ValueError(f"Found more than one range mark in test text in test {test_name}.")
        selected_inserts = insert_map[selected_range]
        for insert in selected_inserts:
            error = [ErrorClass.Character, ErrorClass.Syntax] if insert.outcome == Outcome.FAIL else None
            category = Category.RANGES
            name = f"{insert.name}_in_{test_name}"
            data = (text_front + insert.text + text_back).encode("utf-8")
            test_file = TestFile(name, insert.outcome, content=data, error=error, feature=feature_name, subdir=subdir)
            self.test_files[category].append(test_file)

    def write(self, category: Category, index: int, test_file: TestFile):
        data = self._prepare_test_data(test_file)
        path = self._get_test_file_path(category, index, test_file)
        path.write_bytes(data)
        data = self._prepare_result(test_file)
        if data:
            path = path.with_suffix(".out")
            path.write_bytes(data)

    def _prepare_test_data(self, test_file: TestFile) -> bytes:
        """Prepare the test data from the test file instance."""
        data = b""
        if test_file.add_bom:
            data = b"\xef\xbb\xbf"
        if test_file.content and not test_file.template:
            data += test_file.content
        elif test_file.template:
            template_path: Path = self.template_path / test_file.template
            data += template_path.read_bytes()
            if test_file.content:
                data = data.replace(b"{{content}}", test_file.content)
        return data

    def _prepare_result(self, test_file: TestFile):
        data: Optional[bytes] = None
        if test_file.outcome == Outcome.PASS:
            if test_file.template and not test_file.output:
                out_template_path = (self.template_path / test_file.template).with_suffix(".out")
                if out_template_path.is_file():
                    data = out_template_path.read_bytes()
                    if test_file.content:
                        data = data.replace(b"{{content}}", test_file.content)
            if data is None:
                data = b""
        else:
            if isinstance(test_file.error, list):
                data = f"FAIL = {'|'.join(test_file.error)}\n".encode("utf-8")
            else:
                data = f"FAIL = {test_file.error}\n".encode("utf-8")
        return data

    def _get_test_file_path(self, category: Category, index: int, test_file: TestFile):
        """Create the full path for the resulting test file."""
        path = self.tests_path / test_file.feature / str(category)
        if test_file.subdir:
            path /= test_file.subdir
        file_name = f"{index:04d}-{test_file.outcome}-{test_file.name}.elcl"
        path /= file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def generate(self):
        """Generate all test files."""
        self.initialize_test_files()
        counters: dict[str, int] = defaultdict(int)
        for category in Category:
            category = Category(category)
            for test_file in self.test_files[category]:
                directory = test_file.feature + "/" + str(category)
                if test_file.subdir:
                    directory += "/" + test_file.subdir
                counters[directory] += 1
                index = counters[directory]
                self.write(category, index, test_file)


if __name__ == "__main__":
    ws = WorkingSet()
    ws.generate()
