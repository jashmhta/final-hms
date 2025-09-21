import ast
import re
from pathlib import Path


class XSSFixer(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "format_html" and len(node.args) > 0:
            new_args = []
            for arg in node.args:
                if isinstance(arg, ast.Str):
                    new_args.append(arg)
                elif isinstance(arg, ast.Name):
                    new_args.append(
                        ast.Call(
                            func=ast.Name(id="escape", ctx=ast.Load()),
                            args=[arg],
                            keywords=[],
                        )
                    )
                else:
                    new_args.append(arg)
            node.args = new_args
            ast.fix_missing_locations(node)
        self.generic_visit(node)
        return node


def fix_file(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()
        if "format_html" not in content:
            return
        print(f"Processing {filepath}")
        tree = ast.parse(content, filename=str(filepath))
        fixer = XSSFixer()
        fixed_tree = fixer.visit(tree)
        fixed_content = ast.unparse(fixed_tree)
        if "from django.utils.html import escape" not in fixed_content:
            lines = fixed_content.split("\n")
            import_inserted = False
            for i, line in enumerate(lines):
                if line.startswith("from django.utils.html import"):
                    if "escape" not in line:
                        lines[i] = line.rstrip() + ", escape"
                    import_inserted = True
                    break
                elif line.startswith("from django") and not import_inserted:
                    lines.insert(i, "from django.utils.html import escape")
                    import_inserted = True
                    break
            if not import_inserted:
                lines.insert(0, "from django.utils.html import escape")
            fixed_content = "\n".join(lines)
        backup_path = filepath.with_suffix(".py.backup")
        with open(backup_path, "w") as f:
            f.write(content)
        with open(filepath, "w") as f:
            f.write(fixed_content)
        print(f"Fixed {filepath} (backup: {backup_path})")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")


def main():
    backend_path = Path(__file__).parent.parent.parent / "backend"
    for py_file in backend_path.rglob("*.py"):
        try:
            with open(py_file, "r") as f:
                content = f.read()
                if "format_html" in content:
                    fix_file(py_file)
        except Exception:
            pass
    print("XSS vulnerability fixes complete")


if __name__ == "__main__":
    main()
