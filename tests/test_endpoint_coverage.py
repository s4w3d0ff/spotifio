import ast
import pathlib

SOURCE = pathlib.Path("spotifio")


def _get_only_methods():
    found = set()
    for path in sorted(SOURCE.glob("*.py")):
        tree = ast.parse(path.read_text())
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for fn in [n for n in cls.body if isinstance(n, ast.AsyncFunctionDef)]:
                if fn.name.startswith("_"):
                    continue
                verbs = {
                    call.args[0].value
                    for call in ast.walk(fn)
                    if isinstance(call, ast.Call)
                    and getattr(call.func, "attr", "") == "_request"
                    and call.args and isinstance(call.args[0], ast.Constant)
                }
                if verbs == {"GET"}:
                    found.add(fn.name)
    return found


def test_every_get_only_method_is_named_by_the_live_sweep():
    sweep = pathlib.Path("tests/test_live_api.py").read_text()
    named = {
        node.value
        for node in ast.walk(ast.parse(sweep))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    missing = _get_only_methods() - named
    assert not missing, f"not swept: {sorted(missing)}"
