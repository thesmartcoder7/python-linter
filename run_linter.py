import sys
from linter import Linter

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_linter.py <file_to_lint.py>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r", encoding="utf-8") as f:
        source_code = f.read()

    linter = Linter()
    errors = linter.lint(source_code)

    if errors:
        for error in errors:
            print(f"[{error.rule_name}] Line {error.line_number}: {error.message}")
    else:
        print("No linting issues found!")

if __name__ == "__main__":
    main()
