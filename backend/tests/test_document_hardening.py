import io
import zipfile

import pytest
from fastapi import HTTPException, UploadFile
from pypdf import PdfWriter

from security.file_validation import (
    ALLOWED_TYPES,
    validate_file_signature,
    validate_upload,
)
from ai.lexscan_engine import LexScanEngine
from tools.ocr_processor import OCRProcessor
from tools.ocr_real import RealOCRProcessor


def _docx_bytes(text: str = "Contrato de teste") -> bytes:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        "</Types>"
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>"
        "</w:document>"
    )
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document)
    return target.getvalue()


def test_legacy_doc_is_not_advertised_as_supported():
    assert ".doc" not in ALLOWED_TYPES


def test_disguised_executable_is_rejected_as_pdf():
    with pytest.raises(HTTPException) as error:
        validate_file_signature("peticao.pdf", b"MZ\x90\x00fake executable")

    assert error.value.status_code == 400


def test_docx_container_is_validated(tmp_path):
    content = _docx_bytes()
    path = tmp_path / "contrato.docx"
    path.write_bytes(content)

    mime_type = validate_file_signature(
        path.name,
        content[:8192],
        str(path),
    )

    assert mime_type.endswith("wordprocessingml.document")


@pytest.mark.asyncio
async def test_upload_validator_stops_after_configured_limit():
    upload = UploadFile(
        filename="grande.txt",
        file=io.BytesIO(b"a" * (1024 * 1024 + 1)),
    )

    with pytest.raises(HTTPException) as error:
        await validate_upload(upload, max_size_mb=1)

    assert error.value.status_code == 413


def test_large_text_path_is_sampled_without_full_memory_load(tmp_path):
    path = tmp_path / "processo_grande.txt"
    path.write_bytes(
        b"MARCADOR-INICIO\n"
        + b"x" * 3_000_000
        + b"\nMARCADOR-FINAL"
    )
    processor = RealOCRProcessor()
    processor.max_text_chars = 200_000

    result = processor.process_path(path)

    assert result["success"] is True
    assert result["truncated"] is True
    assert "MARCADOR-INICIO" in result["text"]
    assert "MARCADOR-FINAL" in result["text"]
    assert len(result["text"]) <= 200_000


def test_pdf_page_limit_fails_closed():
    target = io.BytesIO()
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=595, height=842)
    writer.write(target)

    processor = RealOCRProcessor()
    processor.max_pdf_pages = 2
    result = processor.process_document(target.getvalue(), "autos.pdf")

    assert result["success"] is False
    assert "limite seguro" in result["error"]


def test_repeated_deadlines_and_values_are_bounded():
    processor = OCRProcessor()
    text = ("Prazo de 15 dias. Valor R$ 18.750,00.\n" * 5000)

    result = processor.analyze_document(text)

    assert len(result["deadlines"]) == processor.max_extracted_items
    assert len(result["values"]) == processor.max_extracted_items


def test_ai_context_sample_preserves_beginning_middle_and_end():
    text = "INICIO-" + ("a" * 5000) + "-MEIO-" + ("b" * 5000) + "-FINAL"

    sample = LexScanEngine._build_context_sample(text, max_characters=600)

    assert "INICIO" in sample
    assert "MEIO" in sample
    assert "FINAL" in sample
    assert len(sample) < 700
