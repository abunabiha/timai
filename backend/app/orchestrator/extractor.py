import csv
import io
import os
import xml.etree.ElementTree as ET
import zipfile


def extract_text_from_file(filename: str, file_bytes: bytes) -> tuple[str, str]:
    """
    Extracts text content and generates a brief summary from uploaded files.
    Supports PDF, DOCX, CSV, BibTeX, RIS, and plain text formats.
    Returns: (full_text, summary)
    """
    ext = os.path.splitext(filename)[1].lower()
    full_text = ""

    try:
        if ext in (".txt", ".md", ".bib", ".ris"):
            try:
                full_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                full_text = file_bytes.decode("latin-1", errors="replace")

        elif ext == ".csv":
            text_stream = io.StringIO(file_bytes.decode("utf-8", errors="replace"))
            reader = csv.reader(text_stream)
            rows = list(reader)
            if rows:
                headers = rows[0]
                row_count = len(rows) - 1
                sample = "\n".join([", ".join(r) for r in rows[:10]])
                full_text = f"CSV File: {filename}\nHeaders: {', '.join(headers)}\nTotal Rows: {row_count}\nSample:\n{sample}"
            else:
                full_text = "Empty CSV file"

        elif ext == ".docx":
            # Extract text from word/document.xml inside docx zip archive
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
                xml_content = docx_zip.read("word/document.xml")
                root = ET.fromstring(xml_content)
                namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for p in root.findall(".//w:p", namespaces):
                    texts = [t.text for t in p.findall(".//w:t", namespaces) if t.text]
                    if texts:
                        paragraphs.append("".join(texts))
                full_text = "\n\n".join(paragraphs)

        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages_text = [page.extract_text() or "" for page in reader.pages]
                full_text = "\n\n".join(pages_text)
            except Exception:
                # Fallback: basic ASCII/text scan for PDF stream
                ascii_parts = []
                for chunk in file_bytes.split(b"\n"):
                    cleaned = chunk.decode("ascii", errors="ignore").strip()
                    if len(cleaned) > 10 and not cleaned.startswith(("%PDF", "xref", "trailer")):
                        ascii_parts.append(cleaned)
                full_text = "\n".join(ascii_parts[:100])

        else:
            full_text = file_bytes.decode("utf-8", errors="replace")

    except Exception as exc:
        full_text = f"Error extracting content from {filename}: {exc}"

    # Generate a brief 2-3 line summary
    cleaned_lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    preview = " ".join(cleaned_lines[:5])
    summary = f"Dokumen {filename} ({len(file_bytes)} bytes). Pratinjau: {preview[:250]}..." if preview else f"Dokumen {filename}"

    return full_text, summary
