import os

def crawl_files(directory, extensions=None):
    extensions = extensions or [".py", ".md"]
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                matched_files.append(os.path.join(root, file))
    return matched_files
