import re

def preprocess_code(raw_code):
    # Remove single-line comments
    code_without_comments = re.sub(r"#.*", "", raw_code)
    
    # Remove blank lines
    cleaned_code = "\n".join([line.strip() for line in code_without_comments.splitlines() if line.strip()])
    
    return cleaned_code


def extract_docstrings(raw_code):
    docstrings = []
    try:
        import ast
        tree = ast.parse(raw_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node):
                docstrings.append(ast.get_docstring(node))
    except SyntaxError:
        pass
    
    return docstrings


def preprocess_documentation(raw_content):
    # Normalize whitespace
    normalized_content = re.sub(r"\s+", " ", raw_content)
    
    # Return cleaned content
    return normalized_content


def extract_sections(raw_content):
    sections = [line.strip() for line in raw_content.splitlines() if line.startswith("#")]
    return sections
