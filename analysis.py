import os
import ast
from collections import defaultdict
import math

def get_complexity(node):
    complexity = 1
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)):
            complexity += 1
        if isinstance(n, ast.BoolOp) and isinstance(n.op, (ast.And, ast.Or)):
            complexity += len(n.values) - 1
    return complexity

def get_python_files(dirs):
    files = []
    for dir in dirs:
        for root, _, filenames in os.walk(dir):
            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(os.path.join(root, filename))
    return files

def analyze_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content, filepath)
    lines = content.splitlines()
    
    # For functions
    func_complexities = []
    class_hierarchies = defaultdict(list)
    func_lengths = []
    func_params = []
    annotated_funcs = 0
    total_funcs = 0
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            total_funcs += 1
            # Complexity
            comp = get_complexity(node)
            func_complexities.append((node.name, comp))
            # Length
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno') and node.end_lineno is not None and node.lineno is not None:
                length = node.end_lineno - node.lineno + 1
                func_lengths.append((node.name, length))
            # Params
            params = len(node.args.args) + len(node.args.kwonlyargs)
            if node.args.vararg is not None:
                params += 1
            if node.args.kwarg is not None:
                params += 1
            func_params.append((node.name, params))
            # Annotations
            if node.returns or any(arg.annotation for arg in node.args.args + node.args.kwonlyargs):
                annotated_funcs += 1
        elif isinstance(node, ast.ClassDef):
            bases = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
            class_hierarchies[node.name] = bases
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
    
    # Maintainability index
    # Simplified MI = 171 - 5.2 * ln(G) - 0.23 * G - 16.2 * ln(LOC)
    # Where G is average complexity
    if func_complexities and len(lines) > 0:
        avg_g = sum(c for n,c in func_complexities) / len(func_complexities)
        if avg_g > 0:
            mi = 171 - 5.2 * math.log(avg_g) - 0.23 * avg_g - 16.2 * math.log(len(lines))
        else:
            mi = 0
    else:
        mi = 0
    
    # Type coverage
    type_coverage = annotated_funcs / total_funcs if total_funcs > 0 else 0
    
    return {
        'complexities': func_complexities,
        'class_hierarchies': dict(class_hierarchies),
        'func_lengths': func_lengths,
        'func_params': func_params,
        'type_coverage': type_coverage,
        'maintainability_index': mi,
        'imports': imports,
        'loc': len(lines)
    }

def main():
    dirs = ['backend', 'services']
    files = get_python_files(dirs)
    results = {}
    for file in files:
        try:
            results[file] = analyze_file(file)
        except Exception as e:
            results[file] = {'error': str(e)}
    
    # For dependency graph, collect all imports
    all_imports = defaultdict(list)
    for file, data in results.items():
        if 'error' not in data:
            for imp in data['imports']:
                all_imports[imp].append(file)
    
    # Print results
    for file, data in results.items():
        print(f"File: {file}")
        if 'error' in data:
            print(f"  Error: {data['error']}")
            continue
        print(f"  LOC: {data['loc']}")
        print(f"  Maintainability Index: {data['maintainability_index']:.2f}")
        print(f"  Type Coverage: {data['type_coverage']:.2f}")
        print("  Function Complexities:")
        for name, comp in data['complexities']:
            print(f"    {name}: {comp}")
        print("  Function Lengths:")
        for name, length in data['func_lengths']:
            print(f"    {name}: {length}")
        print("  Function Parameters:")
        for name, params in data['func_params']:
            print(f"    {name}: {params}")
        print("  Class Hierarchies:")
        for cls, bases in data['class_hierarchies'].items():
            print(f"    {cls}: {bases}")
        print("  Imports:")
        for imp in data['imports']:
            print(f"    {imp}")
        print()
    
    print("Import Dependency Graph:")
    for imp, files in all_imports.items():
        print(f"  {imp}: {files}")

if __name__ == '__main__':
    main()