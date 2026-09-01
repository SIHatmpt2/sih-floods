import ast
from pathlib import Path


def test_all_processing_python_files_parse():
    root = Path(__file__).parents[1]
    files = sorted(root.rglob("*.py"))
    assert files
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
