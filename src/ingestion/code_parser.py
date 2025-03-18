import ast
from ingestion.data_models import CodeFile, CodeEntity

def parse_code_file(file_path):
    """
    Parses a Python file to extract functions, classes, imports, globals,
    nested entities, call relationships, and docstrings.
    """
    entities = []
    function_calls = []
    imports = []
    global_variables = []
    raw_code = ""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_code = f.read()
            tree = ast.parse(raw_code, filename=file_path)

        for node in ast.walk(tree):
            # Extract functions
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                decorators = [d.id if isinstance(d, ast.Name) else d.attr for d in node.decorator_list]
                entities.append(CodeEntity(
                    name=node.name,
                    type="function",
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=docstring,
                    decorators=decorators
                ))

                # Extract function calls within this function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, (ast.Name, ast.Attribute)):
                        callee = child.func.id if isinstance(child.func, ast.Name) else f"{child.func.value.id}.{child.func.attr}"
                        function_calls.append({
                            "caller": node.name,
                            "callee": callee,
                            "file_path": file_path,
                            "line_number": child.lineno  # Include line number of call
                        })

            # Extract classes
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                bases = [base.id if isinstance(base, ast.Name) else base.attr for base in node.bases]
                entities.append(CodeEntity(
                    name=node.name,
                    type="class",
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=docstring,
                    parents=bases  # Add parent classes
                ))

            # Extract imports
            elif isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.extend([f"{module}.{alias.name}" for alias in node.names])

            # Extract global variables
            elif isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                global_variables.extend([{"name": target, "line_number": node.lineno} for target in targets])

    except (SyntaxError, FileNotFoundError) as e:
        print(f"Error parsing {file_path}: {e}")

    return CodeFile(
        file_path=file_path,
        entities=entities,
        raw_code=raw_code,
        cleaned_code=None,
        docstrings=[entity.docstring for entity in entities if entity.docstring],
        function_calls=function_calls,
        imports=imports,
        global_variables=global_variables
    )
