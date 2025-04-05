import re
from .data_models import DocumentationFile

def preprocess_documentation(raw_content):
    """
    Cleans documentation content by removing unnecessary whitespace and normalizing text.
    
    Args:
        raw_content (str): Raw documentation content as a string.
    
    Returns:
        str: Cleaned documentation content.
    """
    # Normalize whitespace
    cleaned_content = re.sub(r"\s+", " ", raw_content)
    return cleaned_content


def extract_sections(raw_content):
    """
    Extracts sections from documentation based on markdown headers (#).
    
    Args:
        raw_content (str): Raw documentation content as a string.
    
    Returns:
        list: List of section titles found in the documentation.
    """
    sections = [line.strip() for line in raw_content.splitlines() if line.startswith("#")]
    return sections


def extract_api_references(raw_content):
    """
    Extracts API references or function-like patterns from documentation.
    
    Args:
        raw_content (str): Raw documentation content as a string.
    
    Returns:
        list: List of extracted API references or function names.
    """
    api_pattern = r'\b[A-Za-z_]+\([\w\s,]*\)'
    return re.findall(api_pattern, raw_content)


def parse_doc_file(file_path):
    """
    Parses a Markdown file to extract sections, API references, and cleaned content.
    
    Args:
        file_path (str): Path to the Markdown file (.md).
    
    Returns:
        DocumentationFile: A structured representation of the parsed file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # Preprocess content
    cleaned_content = preprocess_documentation(raw_content)

    # Extract metadata
    sections = extract_sections(raw_content)
    api_references = extract_api_references(raw_content)

    return DocumentationFile(
        file_path=file_path,
        sections=sections,
        raw_content=raw_content,
        cleaned_content=cleaned_content,
        api_references=api_references
    )
