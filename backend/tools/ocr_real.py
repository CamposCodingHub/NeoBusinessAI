"""Bounded OCR and text extraction for uploaded documents."""

from __future__ import annotations

import io
import os
import re
import zipfile
from pathlib import Path
from typing import BinaryIO, Dict, Optional, Union
from xml.etree import ElementTree

from PIL import Image
import pytesseract

from config import settings


if os.name == "nt":
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in possible_paths:
        expanded = os.path.expandvars(candidate)
        if os.path.exists(expanded):
            pytesseract.pytesseract.tesseract_cmd = expanded
            break

try:
    from pdf2image import convert_from_bytes, convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class RealOCRProcessor:
    """Extract text with strict memory, page and image limits."""

    def __init__(self):
        self.max_text_chars = settings.MAX_EXTRACTED_TEXT_CHARS
        self.max_pdf_pages = settings.MAX_PDF_PAGES
        self.max_ocr_pages = settings.MAX_OCR_PAGES
        self.max_image_pixels = settings.MAX_IMAGE_PIXELS
        self.tesseract_available = self._check_tesseract()

    @staticmethod
    def _check_tesseract() -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def _limit_text(self, text: str) -> tuple[str, bool]:
        if len(text) <= self.max_text_chars:
            return text.strip(), False
        marker = (
            "\n\n[CONTEUDO TRUNCADO PELO LIMITE DE SEGURANCA; "
            "consulte o arquivo integral para revisao.]\n\n"
        )
        head_size = int(self.max_text_chars * 0.8)
        tail_size = self.max_text_chars - head_size - len(marker)
        return (
            text[:head_size].rstrip() + marker + text[-tail_size:].lstrip(),
            True,
        )

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        if not self.tesseract_available:
            return "[ERRO] Tesseract OCR nao esta instalado"

        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                width, height = image.size
                if width * height > self.max_image_pixels:
                    return (
                        "[ERRO] Imagem excede o limite seguro de "
                        f"{self.max_image_pixels:,} pixels"
                    )
                if image.mode != "RGB":
                    image = image.convert("RGB")
                text = pytesseract.image_to_string(
                    image,
                    config="--oem 3 --psm 6 -l por+eng",
                )
                return self._limit_text(text)[0]
        except Exception as exc:
            return f"[ERRO] Falha ao processar imagem: {exc}"

    @staticmethod
    def _reader_for(source: Union[bytes, str, Path, BinaryIO]):
        if isinstance(source, bytes):
            return PdfReader(io.BytesIO(source))
        return PdfReader(source)

    def _extract_embedded_pdf(
        self,
        source: Union[bytes, str, Path, BinaryIO],
    ) -> tuple[str, int, bool]:
        if not PYPDF_AVAILABLE:
            return "", 0, False

        reader = self._reader_for(source)
        page_count = len(reader.pages)
        if page_count > self.max_pdf_pages:
            raise ValueError(
                f"PDF possui {page_count} paginas; limite seguro: {self.max_pdf_pages}"
            )

        chunks = []
        current_size = 0
        truncated = False
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            block = f"\n--- PAGINA {page_number} ---\n{page_text}"
            if current_size + len(block) > self.max_text_chars:
                remaining = max(self.max_text_chars - current_size, 0)
                if remaining:
                    chunks.append(block[:remaining])
                truncated = True
                break
            chunks.append(block)
            current_size += len(block)
        return "\n".join(chunks).strip(), page_count, truncated

    def _ocr_pdf(
        self,
        source: Union[bytes, str, Path],
        page_count: int,
    ) -> tuple[str, bool]:
        if not self.tesseract_available:
            return "[ERRO] Tesseract OCR nao esta instalado", False
        if not PDF2IMAGE_AVAILABLE:
            return "[ERRO] pdf2image nao esta instalado", False
        if page_count > self.max_ocr_pages:
            return (
                "[ERRO] PDF escaneado possui "
                f"{page_count} paginas; limite de OCR: {self.max_ocr_pages}",
                False,
            )

        chunks = []
        size = 0
        truncated = False
        for page_number in range(1, page_count + 1):
            converter = convert_from_bytes if isinstance(source, bytes) else convert_from_path
            images = converter(
                source,
                dpi=220,
                fmt="png",
                first_page=page_number,
                last_page=page_number,
                thread_count=1,
            )
            if not images:
                continue
            image = images[0]
            try:
                text = pytesseract.image_to_string(
                    image,
                    config="--oem 3 --psm 6 -l por+eng",
                )
            finally:
                image.close()
            block = f"\n--- PAGINA {page_number} ---\n{text.strip()}"
            if size + len(block) > self.max_text_chars:
                remaining = max(self.max_text_chars - size, 0)
                if remaining:
                    chunks.append(block[:remaining])
                truncated = True
                break
            chunks.append(block)
            size += len(block)
        return "\n".join(chunks).strip(), truncated

    def extract_pdf(
        self,
        source: Union[bytes, str, Path],
    ) -> Dict:
        try:
            embedded_text, page_count, truncated = self._extract_embedded_pdf(source)
            if embedded_text:
                return {
                    "success": True,
                    "text": embedded_text,
                    "pages": page_count,
                    "method": "pdf_embedded_text",
                    "truncated": truncated,
                    "error": "",
                }

            if not page_count and PYPDF_AVAILABLE:
                page_count = len(self._reader_for(source).pages)
            ocr_text, ocr_truncated = self._ocr_pdf(source, page_count)
            success = bool(ocr_text.strip()) and not ocr_text.startswith("[ERRO]")
            return {
                "success": success,
                "text": ocr_text if success else "",
                "pages": page_count,
                "method": "tesseract_ocr_pdf",
                "truncated": ocr_truncated,
                "error": "" if success else ocr_text,
            }
        except Exception as exc:
            return {
                "success": False,
                "text": "",
                "pages": 0,
                "method": "pdf_failed",
                "truncated": False,
                "error": f"Falha ao processar PDF: {exc}",
            }

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Backward-compatible PDF extraction method."""
        result = self.extract_pdf(pdf_bytes)
        return result["text"] if result["success"] else f"[ERRO] {result['error']}"

    @staticmethod
    def extract_text_file(file_bytes: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return file_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace").strip()

    def extract_text_path(self, file_path: Union[str, Path]) -> tuple[str, bool]:
        """Sample the beginning and end without loading a large text file."""
        path = Path(file_path)
        byte_budget = self.max_text_chars * 2
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size <= byte_budget:
                data = handle.read()
            else:
                head_size = int(byte_budget * 0.8)
                tail_size = byte_budget - head_size
                head = handle.read(head_size)
                handle.seek(max(size - tail_size, 0))
                tail = handle.read(tail_size)
                data = (
                    head
                    + b"\n\n[AMOSTRA INTERMEDIARIA OMITIDA POR SEGURANCA]\n\n"
                    + tail
                )
        text = self.extract_text_file(data)
        limited_text, limited = self._limit_text(text)
        return limited_text, size > byte_budget or limited

    def extract_text_from_rtf(self, file_bytes: bytes) -> str:
        raw = self.extract_text_file(file_bytes)
        raw = re.sub(r"\\par[d]?\b", "\n", raw)
        raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
        raw = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", raw)
        raw = raw.replace("{", "").replace("}", "")
        return self._limit_text(re.sub(r"[ \t]+", " ", raw).strip())[0]

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                info = archive.getinfo("word/document.xml")
                if info.file_size > 25 * 1024 * 1024:
                    return "[ERRO] Conteudo interno do DOCX excede o limite seguro"
                document_xml = archive.read(info)
            root = ElementTree.fromstring(document_xml)
            paragraphs = []
            size = 0
            for paragraph in root.iter():
                if not paragraph.tag.endswith("}p"):
                    continue
                text = "".join(
                    node.text or ""
                    for node in paragraph.iter()
                    if node.tag.endswith("}t")
                ).strip()
                if not text:
                    continue
                remaining = self.max_text_chars - size
                if remaining <= 0:
                    break
                paragraphs.append(text[:remaining])
                size += len(text) + 1
            return "\n".join(paragraphs).strip()
        except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            return f"[ERRO] Falha ao extrair DOCX: {exc}"

    def _result(
        self,
        filename: str,
        document_type: str,
        text: str,
        method: str,
        pages: int = 1,
        truncated: bool = False,
    ) -> Dict:
        success = bool(text.strip()) and not text.startswith("[ERRO]")
        return {
            "success": success,
            "filename": filename,
            "type": document_type,
            "text": text if success else "",
            "pages": pages,
            "method": method,
            "truncated": truncated,
            "error": "" if success else text,
        }

    def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        manual_text: Optional[str] = None,
    ) -> Dict:
        if manual_text:
            text, truncated = self._limit_text(manual_text)
            return self._result(
                filename,
                "manual",
                text,
                "manual_input",
                truncated=truncated,
            )

        extension = Path(filename).suffix.lower()
        if extension == ".txt":
            text, truncated = self._limit_text(self.extract_text_file(file_bytes))
            return self._result(filename, "text", text, "text_decode", truncated=truncated)
        if extension == ".rtf":
            text = self.extract_text_from_rtf(file_bytes)
            return self._result(
                filename,
                "rtf",
                text,
                "rtf_parser",
                truncated=len(text) >= self.max_text_chars - 2,
            )
        if extension == ".docx":
            text = self.extract_text_from_docx(file_bytes)
            return self._result(
                filename,
                "docx",
                text,
                "docx_xml",
                truncated=len(text) >= self.max_text_chars,
            )
        if extension == ".pdf":
            return {"filename": filename, "type": "pdf", **self.extract_pdf(file_bytes)}
        if extension in {".jpg", ".jpeg", ".png", ".tiff", ".tif"}:
            text = self.extract_text_from_image(file_bytes)
            return self._result(filename, "image", text, "tesseract_ocr")
        return self._result(
            filename,
            "unknown",
            "[ERRO] Formato nao suportado. Use PDF, DOCX, TXT, RTF, JPG, PNG ou TIFF.",
            "unsupported",
        )

    def process_path(
        self,
        file_path: Union[str, Path],
        filename: Optional[str] = None,
    ) -> Dict:
        path = Path(file_path)
        display_name = filename or path.name
        extension = path.suffix.lower()

        if extension == ".txt":
            text, truncated = self.extract_text_path(path)
            return self._result(
                display_name,
                "text",
                text,
                "streamed_text_sample",
                truncated=truncated,
            )
        if extension == ".pdf":
            return {"filename": display_name, "type": "pdf", **self.extract_pdf(path)}

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        with path.open("rb") as handle:
            file_bytes = handle.read(max_bytes + 1)
        if len(file_bytes) > max_bytes:
            return self._result(
                display_name,
                "unknown",
                "[ERRO] Arquivo excede o limite configurado",
                "size_limit",
            )
        return self.process_document(file_bytes, display_name)


ocr_real = RealOCRProcessor()


def process_uploaded_file(
    file_bytes: bytes,
    filename: str,
    manual_text: Optional[str] = None,
) -> Dict:
    return ocr_real.process_document(file_bytes, filename, manual_text)


def process_uploaded_path(file_path: Union[str, Path], filename: Optional[str] = None) -> Dict:
    return ocr_real.process_path(file_path, filename)


if __name__ == "__main__":
    print(
        {
            "tesseract_available": ocr_real.tesseract_available,
            "max_pdf_pages": ocr_real.max_pdf_pages,
            "max_ocr_pages": ocr_real.max_ocr_pages,
            "max_text_chars": ocr_real.max_text_chars,
        }
    )
