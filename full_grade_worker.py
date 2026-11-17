"""Bounded offline inspector process, without loading provider SDKs.

Only a named function from trusted, frozen repository source is compiled. Loading
the entire pilot modules would initialize expensive provider imports for every
file. Artifact bytes are data and are never compiled or executed.
"""

import argparse
import ast
import base64
import io
import json
from pathlib import Path


def helper(filename, name, extra=None):
    source = Path(__file__).with_name(filename)
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    namespace = {"Path": Path, "base64": base64, "io": io, **(extra or {})}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
    return namespace[name]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["inspect", "view"])
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--page", type=int, default=1)
    args = parser.parse_args()
    if args.operation == "inspect":
        result = helper("pilot_grade.py", "inspect_file")(args.file)
    else:
        from PIL import Image

        result = helper("pilot_tools.py", "view", {"Image": Image})(str(args.file.relative_to(args.context)), args.context, args.page)
    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
