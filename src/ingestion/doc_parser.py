# import re
# from .data_models import DocumentationFile

# def preprocess_documentation(raw_content):
#     """
#     Cleans documentation content by removing unnecessary whitespace and normalizing text.
    
#     Args:
#         raw_content (str): Raw documentation content as a string.
    
#     Returns:
#         str: Cleaned documentation content.
#     """
#     # Normalize whitespace
#     cleaned_content = re.sub(r"\s+", " ", raw_content)
#     return cleaned_content


# def extract_sections(raw_content):
#     """
#     Extracts sections from documentation based on markdown headers (#).
    
#     Args:
#         raw_content (str): Raw documentation content as a string.
    
#     Returns:
#         list: List of section titles found in the documentation.
#     """
#     sections = [line.strip() for line in raw_content.splitlines() if line.startswith("#")]
#     return sections


# def extract_api_references(raw_content):
#     """
#     Extracts API references or function-like patterns from documentation.
    
#     Args:
#         raw_content (str): Raw documentation content as a string.
    
#     Returns:
#         list: List of extracted API references or function names.
#     """
#     api_pattern = r'\b[A-Za-z_]+\([\w\s,]*\)'
#     return re.findall(api_pattern, raw_content)


# def parse_doc_file(file_path):
#     """
#     Parses a Markdown file to extract sections, API references, and cleaned content.
    
#     Args:
#         file_path (str): Path to the Markdown file (.md).
    
#     Returns:
#         DocumentationFile: A structured representation of the parsed file.
#     """
#     with open(file_path, "r", encoding="utf-8") as f:
#         raw_content = f.read()

#     # Preprocess content
#     cleaned_content = preprocess_documentation(raw_content)

#     # Extract metadata
#     sections = extract_sections(raw_content)
#     api_references = extract_api_references(raw_content)

#     return DocumentationFile(
#         file_path=file_path,
#         sections=sections,
#         raw_content=raw_content,
#         cleaned_content=cleaned_content,
#         api_references=api_references
#     )

import re
from src.utils.logging_utils import setup_logger
from .data_models import DocumentationFile

logger = setup_logger()

def parse_doc_file(file_path):
    """
    Parses a documentation file (like Markdown) to extract sections,
    content, and API references.
    """
    sections = []
    raw_content = ""
    api_references = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        
        # Extract headers/sections using regex
        # Match Markdown headers (# Header, ## Subheader, etc.)
        section_pattern = r'^(#{1,6})\s+(.+?)$'
        for match in re.finditer(section_pattern, raw_content, re.MULTILINE):
            level = len(match.group(1))  # Number of # symbols
            title = match.group(2).strip()
            sections.append(title)
        
        # Extract potential API references - multiple approaches
        
        # 1. Code block references (``````)
        code_block_pattern = r'``````'
        for match in re.finditer(code_block_pattern, raw_content, re.DOTALL):
            code_content = match.group(1)
            # Look for function/class definitions or imports in code blocks
            func_pattern = r'def\s+([a-zA-Z0-9_]+)'
            class_pattern = r'class\s+([a-zA-Z0-9_]+)'
            import_pattern = r'(?:from|import)\s+([a-zA-Z0-9_.]+)'
            
            for pattern in [func_pattern, class_pattern, import_pattern]:
                for func_match in re.finditer(pattern, code_content):
                    api_references.append(func_match.group(1))
        
        # 2. Inline code references (`package.function`)
        inline_code_pattern = r'`([a-zA-Z0-9_.]+\.[a-zA-Z0-9_]+)`'
        for match in re.finditer(inline_code_pattern, raw_content):
            api_references.append(match.group(1))
        
        # 3. Link references [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, raw_content):
            link_text = match.group(1)
            link_url = match.group(2)
            # Only include API references, not all links
            if 'api' in link_url.lower() or 'doc' in link_url.lower():
                api_references.append(f"{link_text} ({link_url})")
        
        # Remove duplicates and sort
        api_references = sorted(list(set(api_references)))
        
        # Basic cleaning for cleaned_content
        # Remove extra whitespace but preserve structure
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', raw_content)
        
    except FileNotFoundError as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return None
    
    doc_file = DocumentationFile(
        file_path=file_path,
        sections=sections,
        raw_content=raw_content,
        cleaned_content=cleaned_content,
        api_references=", ".join(api_references),
        embedding_id=-1,
        type="DocumentationFile.class"
    )
    
    logger.info(f"Parsed {file_path} successfully")
    return doc_file