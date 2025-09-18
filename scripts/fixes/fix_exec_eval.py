import ast
import os
import shutil
from pathlib import Path
class ExecEvalFixer(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ["exec", "eval"]:
                if func_name == "exec":
                    print(
                        f"MANUAL REVIEW NEEDED: exec at {node.lineno} - cannot auto-fix safely"
                    )
                    return node
                else:  
                    new_node = ast.Call(
                        func=ast.Name(id="ast.literal_eval", ctx=ast.Load()),
                        args=[
                            ast.Call(
                                func=ast.Name(id="str", ctx=ast.Load()),
                                args=[node.args[0]],
                                keywords=[],
                            )
                        ],
                        keywords=[],
                    )
                    ast.fix_missing_locations(new_node)
                    return new_node
        self.generic_visit(node)
        return node
def fix_file(filepath):
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        fixer = ExecEvalFixer()
        fixed_tree = fixer.visit(tree)
        backup_path = filepath.with_suffix(".py.backup")
        shutil.copy2(filepath, backup_path)
        with open(filepath, "w") as f:
            f.write(ast.unparse(fixed_tree))
        print(f"Fixed {filepath} (backup: {backup_path})")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
root_dir = Path("/root/hms-enterprise-grade/backend")
backend_services = ["appointments", "billing", "patients", "lab", "radiology", "ehr"]
for service in backend_services:
    service_path = root_dir / service
    if service_path.exists():
        for py_file in service_path.rglob("*.py"):
            fix_file(py_file)
print("Exec/eval fix complete")