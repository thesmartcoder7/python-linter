# Python Linter

## Overview
This is a custom Python linter that checks for three specific issues in Python code:
- **Unused Imports**: Detects imports that are never used.
- **Unused Variables**: Identifies variables that are defined but never referenced.
- **Duplicate Dictionary Keys**: Warns if a dictionary contains repeated keys.

The linter traverses the Abstract Syntax Tree (AST) of Python code to identify and report these issues.

## Features
- Detects and reports unused imports.
- Identifies variables that are declared but never used.
- Flags duplicate dictionary keys that might cause unexpected behavior.
- Provides detailed error messages with line numbers.

## Installation
No external dependencies are required beyond Python's standard library. Ensure you have Python 3.7+ installed.

Clone the repository:
```sh
git clone https://github.com/thesmartcoder7/python-linter.git
cd python-linter
```

## Usage
To lint a Python file, run the following command:
```sh
python main.py path/to/your_script.py
```

### Example
Given the following Python script (`example.py`):
```python
import os
import sys  # Unused import

def my_function():
    x = 10  # Unused variable
    y = 20
    print(y)

my_dict = {"a": 1, "b": 2, "a": 3}  # Duplicate key "a"
```
Running the linter:
```sh
python main.py example.py
```
Would produce the following output:
```
[unused_import] Line 2: Imported name 'sys' is unused
[unused_variable] Line 9: Variable 'lyric' is unused
[unused_variable] Line 10: Variable 'test' is unused
```

## How It Works
### Abstract Syntax Tree (AST)
The linter uses Python's built-in `ast` module to parse and analyze code without executing it. The AST allows us to:
- Identify imports and determine if they are used.
- Track variable definitions and check if they are referenced later.
- Detect repeated keys in dictionaries.

### Linter Rules
The linter consists of the following rules:
- **UnusedImportsRule**: Tracks imported names and checks if they appear in the code.
- **UnusedVariablesRule**: Maintains a scope stack to track variable definitions and usage.
- **DuplicateDictKeysRule**: Detects duplicate keys in dictionaries.

### Linter Class
The `Linter` class orchestrates the process:
1. It parses the source code into an AST.
2. It applies each rule to the AST.
3. It collects and sorts lint errors before displaying them.

## Contributing
Feel free to contribute by submitting pull requests or opening issues. Suggestions for additional linting rules are welcome!

## License
This project is licensed under the MIT License.

---
Happy linting! 🚀
