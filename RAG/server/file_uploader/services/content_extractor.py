from .markdown_converter import (
    extract_markdown_from_pdf,
    extract_markdown_from_docx,
    extract_markdown_from_xlsx,
    extract_markdown_from_image,
    extract_markdown_from_csv
)

class ContentExtractor:
    EXTRACTORS = {
        'application/pdf': extract_markdown_from_pdf,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': extract_markdown_from_docx,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': extract_markdown_from_xlsx,
        'text/csv': extract_markdown_from_csv,
        'image/png': extract_markdown_from_image,
        'image/jpeg': extract_markdown_from_image,
        'application/octet-stream': lambda file_path: open(file_path).read()
    }

    @classmethod
    def extract_content(cls, file_path, content_type):
        print(f"Extracting content from {content_type}")
        extractor = cls.EXTRACTORS.get(content_type)
        if extractor:
            return extractor(file_path)
        return None