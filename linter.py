import ast
import sys
import builtins
from collections import defaultdict
from dataclasses import dataclass

BUILTIN_NAMES = set(dir(builtins))

@dataclass
class LintError:
    rule_name: str
    message: str
    line_number: int


class BaseLintRule(ast.NodeVisitor):
    def __init__(self, rule_name: str) -> None:
        self.errors: list[LintError] = []
        self.rule_name: str = rule_name


class UnusedImportsRule(BaseLintRule):
    def __init__(self, rule_name: str) -> None:
        super().__init__(rule_name)
        self.imports: list[tuple[str, int]] = []
        self.used_imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports.append((name, node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports.append((name, node.lineno))
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.used_imports.add(node.id)
        self.generic_visit(node)

    def check(self, tree: ast.AST) -> list[LintError]:
        self.imports = []
        self.used_imports = set()
        self.visit(tree)
        errors = []
        imported_names = set()
        for name, lineno in self.imports:
            if name not in imported_names:
                imported_names.add(name)
                if name not in self.used_imports:
                    errors.append(LintError(
                        rule_name=self.rule_name,
                        message=f"Imported name '{name}' is unused",
                        line_number=lineno
                    ))
            else:
                if name not in self.used_imports:
                    errors.append(LintError(
                        rule_name=self.rule_name,
                        message=f"Imported name '{name}' is unused",
                        line_number=lineno
                    ))
        self.errors = errors
        return self.errors


class UnusedVariablesRule(BaseLintRule):
    def __init__(self, rule_name: str) -> None:
        super().__init__(rule_name)
        self.scopes: list[dict[str, tuple[int, bool]]] = []
        self.current_scope: dict[str, tuple[int, bool]] | None = None

    def _enter_scope(self) -> None:
        self.scopes.append({})
        self.current_scope = self.scopes[-1]

    def _exit_scope(self) -> None:
        if not self.scopes:
            return
        current_scope = self.scopes.pop()
        self.current_scope = self.scopes[-1] if self.scopes else None
        for var, (line, used) in current_scope.items():
            if not used:
                self.errors.append(LintError(
                    rule_name=self.rule_name,
                    message=f"Variable '{var}' is unused",
                    line_number=line
                ))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_scope()
        for arg in node.args.posonlyargs:
            self._record_variable(arg.arg, node.lineno)
        for arg in node.args.args:
            self._record_variable(arg.arg, node.lineno)
        if node.args.vararg:
            self._record_variable(node.args.vararg.arg, node.lineno)
        for arg in node.args.kwonlyargs:
            self._record_variable(arg.arg, node.lineno)
        if node.args.kwarg:
            self._record_variable(node.args.kwarg.arg, node.lineno)
        self.generic_visit(node)
        self._exit_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._enter_scope()
        self.generic_visit(node)
        self._exit_scope()

    def _handle_comprehension(self, node) -> None:
        self._enter_scope()
        for generator in node.generators:
            self._handle_target(generator.target)
        self.generic_visit(node)
        self._exit_scope()

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._handle_comprehension(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._handle_comprehension(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._handle_comprehension(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._handle_comprehension(node)

    def _handle_target(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self._record_variable(target.id, target.lineno)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._handle_target(elt)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._handle_assignment_target(target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._handle_assignment_target(node.target)
        self.generic_visit(node)

    def _handle_assignment_target(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self._record_variable(target.id, target.lineno)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._handle_assignment_target(elt)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            var_name = node.id
            for scope in reversed(self.scopes):
                if var_name in scope:
                    line, _ = scope[var_name]
                    scope[var_name] = (line, True)
                    break
        self.generic_visit(node)

    def _record_variable(self, name: str, lineno: int) -> None:
        if name.startswith('_') or name in BUILTIN_NAMES:
            return
        if self.current_scope is not None and name not in self.current_scope:
            self.current_scope[name] = (lineno, False)

    def check(self, tree: ast.AST) -> list[LintError]:
        self.scopes = []
        self.current_scope = None
        self._enter_scope()
        self.visit(tree)
        self._exit_scope()
        return self.errors


class DuplicateDictKeysRule(BaseLintRule):
    def visit_Dict(self, node: ast.Dict) -> None:
        seen = defaultdict(list)
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant):
                metadata = {"lineno": key.lineno, "key": key.value}
                seen[key.value].append(metadata)
            if isinstance(value, ast.Dict):
                self.visit(value)

        for key, metadata in seen.items():
            if len(metadata) > 1:
                lines = ", ".join(str(line["lineno"]) for line in metadata)
                self.errors.append(
                    LintError(
                        rule_name=self.rule_name,
                        message=f'Key "{key}" has been repeated on lines {lines}',
                        line_number=metadata[0]["lineno"],
                    )
                )

    def check(self, tree: ast.AST) -> list[LintError]:
        self.visit(tree)
        return self.errors


class Linter:
    def __init__(self) -> None:
        self.rules = [
            UnusedImportsRule(rule_name="unused_import"),
            UnusedVariablesRule(rule_name="unused_variable"),
            DuplicateDictKeysRule(rule_name="duplicate_dict_keys"),
        ]

    def lint(self, source_code: str) -> list[LintError]:
        tree = ast.parse(source_code)
        errors: list[LintError] = []

        for rule in self.rules:
            errors.extend(rule.check(tree))

        return sorted(errors, key=lambda e: e.line_number)
