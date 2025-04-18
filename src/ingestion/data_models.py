from dataclasses import asdict, dataclass, field, is_dataclass
from typing import List, Dict, Optional

@dataclass
class FunctionCall:
    """
    Represents a relationship between two functions (caller → callee).
    
    Attributes:
        caller (str): Name of the calling function.
        callee (str): Name of the called function.
        file_path (str): Path to the file where the call occurs.
        line_number (int): Line number where the call occurs.
    """
    caller: str
    callee: str
    file_path: str
    line_number: int


@dataclass
class CodeEntity:
    """
    Represents a function or class definition in source code.
    
    Attributes:
        name (str): Name of the entity (function/class).
        type (str): Type of entity ("function" or "class").
        file_path (str): Path to the file where the entity is defined.
        line_number (int): Line number where the entity is defined.
        docstring (Optional[str]): Docstring associated with the entity (if available).
        decorators (List[str]): List of decorators applied to the entity.
        parents (List[str]): Parent classes for class definitions (empty for functions).
    """
    name: str
    type: str  # "function" or "class"
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)


@dataclass
class CodeFile:
    """
    Represents a source code file with its entities and raw content.
    
    Attributes:
        file_path (str): Path to the source code file.
        entities (List[CodeEntity]): List of functions/classes defined in the file.
        raw_code (str): Raw content of the source code file.
        cleaned_code (Optional[str]): Preprocessed content of the source code file.
        docstrings (List[str]): List of extracted docstrings from the file.
        function_calls (List[FunctionCall]): List of function call relationships within the file.
        imports (List[str]): List of modules imported in this file.
        globals (List[Dict[str, int]]): List of global variables with their line numbers.
    """
    embedding_ids: List[int]
    file_path: str
    entities: List[CodeEntity] = field(default_factory=list)
    raw_code: str = ""
    cleaned_code: Optional[str] = None
    docstrings: List[str] = field(default_factory=list)
    function_calls: List[FunctionCall] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    global_variables: List[Dict[str, int]] = field(default_factory=list)
    type: str = "CodeFile.class"

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "entities": [asdict(e) if is_dataclass(e) else e for e in self.entities],
            "raw_code": self.raw_code,
            "cleaned_code": self.cleaned_code,
            "docstrings": self.docstrings,
            "function_calls": [asdict(fc) if is_dataclass(fc) else fc for fc in self.function_calls], 
            "imports": self.imports,
            "global_variables": self.global_variables,
            "embedding_ids": self.embedding_ids,
            "type": self.type
        }


@dataclass
class DocumentationFile:
    """
    Represents a documentation file with its sections and raw content.
    
    Attributes:
        file_path (str): Path to the documentation file (.md).
        sections (List[str]): List of section headers found in the documentation.
        raw_content (str): Raw content of the documentation file.
        cleaned_content (Optional[str]): Preprocessed content of the documentation file.
    """
    file_path: str
    sections: List[str] = field(default_factory=list)
    raw_content: str = ""
    cleaned_content: Optional[str] = None
    api_references: str = ""


@dataclass
class IngestedData:
    """
    Represents all ingested data from a project directory, including code files and documentation files.
    
    Attributes:
        code_files (List[CodeFile]): List of parsed source code files.
        documentation_files (List[DocumentationFile]): List of parsed documentation files.
        total_files (int): Total number of files processed during ingestion.
    """
    code_files: List[CodeFile] = field(default_factory=list)
    documentation_files: List[DocumentationFile] = field(default_factory=list)
