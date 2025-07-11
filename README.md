
# Erbsland Configuration Language – Conformance Test Suite

The Erbsland Configuration Language (*ELCL*) is a human-friendly format for configuration files. It is designed with clarity and simplicity in mind, making it easy to read and write for both developers and end-users.

This repository contains the official conformance test suite for *ELCL*. Its purpose is to verify that a configuration parser adheres to the language specification and behaves as expected.

## Before You Start

To understand how this test suite works, please refer to the official documentation. It includes a dedicated chapter called “The Test Suite”, where you’ll find detailed explanations about the file structure and expected output format.

👉 [Open the Documentation](https://erbsland-dev.github.io/erbsland-lang-config-doc/)

## Common Questions and Bug Reports

If you have questions about a specific test case or the results from this test suite, you're welcome to start a discussion in the [Discussions](https://github.com/erbsland-dev/erbsland-lang-config-tests/discussions) section.

If you think you've found a bug, an issue in one of the tests or a missing test case, please also begin by opening a [discussion](https://github.com/erbsland-dev/erbsland-lang-config-tests/discussions). This gives us a chance to understand the problem better before moving on to an issue or pull request.

Thanks for contributing to the improvement of this project!

## Running the Conformance Tests

To run the conformance tests, you’ll need to implement a test adapter as described in the documentation under [“Writing a Test Adapter”](https://erbsland-dev.github.io/erbsland-lang-config-doc/tests/test-adapter.html).

### 1. Clone the Repository

```shell
git clone https://github.com/erbsland-dev/erbsland-lang-config-tests.git
```

### 2. Execute the Test Script

Make sure you have Python 3.12 or newer installed.

```shell
cd erbsland-lang-config-tests
python3 conformance_test.py /path/to/test_adapter 
```

**Sample Output**:

```text
Erbsland Configuration Language - Conformance Test
------------------------------------------------------------------------------
Scanning all test cases for tier 'full'...
Running all tests...
-*==========================================================================*-

                    +*+    Conformance test PASSED    +*+

    100.00% tests passed (10311/10311)

    Full-Tier Parser Score: 103110

-*==========================================================================*-
```

## Command Line Options and Exit Code

### `-h`, `--help`

Displays a help message with all available command-line options.

```text
usage: conformance_test.py [-h] [-s] [-f FORMAT] [-o OUTPUT] [-t TIER] [-l LANG_VERSION] testadapter

Test the conformance of a configuration parser.

positional arguments:
  testadapter           Path to the test adapter executable.

options:
  -h, --help            show this help message and exit
  -s, --silent          Disable all progress output.
  -f, --format FORMAT   Output format. Either 'text' or 'json'. Default is 'text'.
  -o, --output OUTPUT   Write all output to this path.
  -t, --tier TIER       Select the parser tier. Select 'minimal', 'standard', or 'full'. Default is 'full'.
  -l, --lang-version LANG_VERSION
                        Select the language version to test. The default and currently the only possible version is
                        '1.0'.
```

### `-s`, `--silent`

Suppresses all progress output. Only the final result will be printed.

### `-f`, `--format`

Sets the output format to either text (human-readable, default) or json (for use in CI pipelines or automated tools).

### `-o`, `--output`

Saves the output to the specified file. Note that progress output is not included in the file.

### `-t`, `--tier`

Specifies the parser tier to test. Valid values are `minimal`, `standard`, and `full`. The default is `full`.

### `-l`, `--lang-version`

Selects the language version to test. Currently, only version `1.0` is supported, which is also the default.

### Exit Code

- `0`: All tests passed successfully.
- `1`: Some tests failed.
- `2`: An unexpected error occurred during test execution.

## License

Copyright © 2025 Tobias Erbsland – https://erbsland.dev/

Licensed under the **Apache License, Version 2.0**.

You may get a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Distributed on an “AS IS” basis, without warranties or conditions of any kind. See the LICENSE file for details.

