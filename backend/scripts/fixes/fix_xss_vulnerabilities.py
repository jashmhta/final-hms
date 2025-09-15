#!/usr/bin/env python
"""
Fix XSS vulnerabilities in Django templates and views
"""

import ast
import re
from pathlib import Path


class XSSFixer(ast.NodeTransformer):
    """AST transformer to fix XSS vulnerabilities"""

    def visit_Call(self, node):
        # Look for format_html calls without proper escaping
        if (isinstance(node.func, ast.Name) and node.func.id == 'format_html' and
            len(node.args) > 0):
            # Check if arguments are properly escaped
            new_args = []
            for arg in node.args:
                if isinstance(arg, ast.Str):
                    # String literals should be safe, but let's be cautious
                    new_args.append(arg)
                elif isinstance(arg, ast.Name):
                    # Variable - should be escaped
                    new_args.append(ast.Call(
                        func=ast.Name(id='escape', ctx=ast.Load()),
                        args=[arg],
                        keywords=[]
                    ))
                else:
                    new_args.append(arg)

            node.args = new_args
            ast.fix_missing_locations(node)

        self.generic_visit(node)
        return node


def fix_file(filepath):
    """Fix XSS vulnerabilities in a Python file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Check if file uses format_html
        if 'format_html' not in content:
            return

        print(f"Processing {filepath}")

        # Parse AST
        tree = ast.parse(content, filename=str(filepath))

        # Apply fixes
        fixer = XSSFixer()
        fixed_tree = fixer.visit(tree)

        # Convert back to code
        fixed_content = ast.unparse(fixed_tree)

        # Add escape import if needed
        if 'from django.utils.html import escape' not in fixed_content:
            # Find import section
            lines = fixed_content.split('\n')
            import_inserted = False

            for i, line in enumerate(lines):
                if line.startswith('from django.utils.html import'):
                    if 'escape' not in line:
                        lines[i] = line.rstrip() + ', escape'
                    import_inserted = True
                    break
                elif line.startswith('from django') and not import_inserted:
                    lines.insert(i, 'from django.utils.html import escape')
                    import_inserted = True
                    break

            if not import_inserted:
                # Add at the beginning
                lines.insert(0, 'from django.utils.html import escape')

            fixed_content = '\n'.join(lines)

        # Backup original
        backup_path = filepath.with_suffix('.py.backup')
        with open(backup_path, 'w') as f:
            f.write(content)

        # Write fixed content
        with open(filepath, 'w') as f:
            f.write(fixed_content)

        print(f"Fixed {filepath} (backup: {backup_path})")

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")


def main():
    """Main fix function"""
    backend_path = Path(__file__).parent.parent.parent / 'backend'

    # Find all Python files that use format_html
    for py_file in backend_path.rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                if 'format_html' in content:
                    fix_file(py_file)
        except Exception:
            pass

    print("XSS vulnerability fixes complete")


if __name__ == '__main__':
    main()