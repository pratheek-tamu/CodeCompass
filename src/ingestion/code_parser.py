import ast
from src.utils.logging_utils import setup_logger
from .data_models import CodeFile, CodeEntity, FunctionCall

logger = setup_logger()

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
                
                # Safely extract decorators
                decorators = [
                    d.id if isinstance(d, ast.Name) else (d.attr if isinstance(d, ast.Attribute) else None)
                    for d in node.decorator_list
                ]
                decorators = [d for d in decorators if d is not None]  # Remove None values
                
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
                    if isinstance(child, ast.Call):  # Ensure `child` is a function call
                        if isinstance(child.func, ast.Name):
                            callee = child.func.id
                        elif isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                            callee = f"{child.func.value.id}.{child.func.attr}"
                        else:
                            callee = None  # Handle unexpected cases

                        if callee:
                            function_calls.append(FunctionCall(
                                caller=node.name,
                                callee=callee,
                                file_path=file_path,
                                line_number=child.lineno
                            ))

            # Extract classes
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)

                # Extract base classes safely
                bases = [
                    base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else None)
                    for base in node.bases
                ]
                bases = [b for b in bases if b is not None]  # Remove None values

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
        logger.error(f"Error parsing {file_path}: {e}")
        return None

    codefile = CodeFile(
        file_path=file_path,
        entities=entities,
        raw_code=raw_code,
        cleaned_code=None,
        docstrings=[entity.docstring for entity in entities if entity.docstring],
        function_calls=function_calls,
        imports=imports,
        global_variables=global_variables
    )
    logger.info(f"Parsed {file_path} successfully")
    return codefile
