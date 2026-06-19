"""Secure validation helpers for uploaded professional documents."""

from __future__ import annotations

import os
import re
import uuid
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import HTTPException, UploadFile

try:
    import magic  # type: ignore

    LIBMAGIC_AVAILABLE = True
except ImportError:
    magic = None
    LIBMAGIC_AVAILABLE = False


MAGIC_NUMBERS = {
    b"%PDF": "application/pdf",
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument",
    b"\x49\x49\x2a\x00": "image/tiff",
    b"\x4d\x4d\x00\x2a": "image/tiff",
}

ALLOWED_TYPES = {
    ".pdf": ["application/pdf"],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ],
    ".txt": ["text/plain"],
    ".rtf": ["application/rtf", "text/rtf"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".png": ["image/png"],
    ".tiff": ["image/tiff"],
    ".tif": ["image/tiff"],
}

MIME_ALIASES = {
    "application/x-pdf": "application/pdf",
    "application/zip": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    "application/x-zip-compressed": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    "image/jpg": "image/jpeg",
}

DANGEROUS_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".sh",
    ".php",
    ".jsp",
    ".asp",
    ".aspx",
    ".py",
    ".rb",
    ".pl",
    ".cgi",
    ".jar",
    ".war",
    ".ear",
    ".bin",
    ".scr",
    ".msi",
    ".vbs",
    ".js",
    ".wsf",
    ".ps1",
    ".htaccess",
    ".env",
}


def validate_filename(filename: str) -> str:
    """Validate the filename and return its accepted extension."""
    if not filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    normalized = filename.strip().lower().replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    parts = basename.split(".")
    if len(parts) > 2 and f".{parts[-1]}" in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Arquivo potencialmente perigoso detectado (extensao dupla)",
        )

    file_ext = os.path.splitext(basename)[1]
    if file_ext in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensao de arquivo nao permitida: {file_ext}",
        )
    if file_ext not in ALLOWED_TYPES:
        allowed = ", ".join(sorted(ALLOWED_TYPES))
        raise HTTPException(
            status_code=400,
            detail=f"Extensao nao permitida. Use: {allowed}",
        )
    return file_ext


def _detect_mime(header: bytes) -> Optional[str]:
    for magic_bytes, mime_type in MAGIC_NUMBERS.items():
        if header.startswith(magic_bytes):
            return mime_type
    if header.lstrip().startswith(b"{\\rtf"):
        return "application/rtf"
    if header and b"\x00" not in header:
        return "text/plain"
    return None


def _validate_docx_archive(file_path: str) -> None:
    try:
        with zipfile.ZipFile(file_path) as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "word/document.xml"}
            if not required.issubset(names):
                raise HTTPException(
                    status_code=400,
                    detail="O arquivo ZIP nao possui a estrutura obrigatoria de um DOCX",
                )

            document_info = archive.getinfo("word/document.xml")
            if document_info.file_size > 25 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="DOCX possui conteudo interno excessivamente grande",
                )
            compressed_size = max(document_info.compress_size, 1)
            if document_info.file_size / compressed_size > 150:
                raise HTTPException(
                    status_code=400,
                    detail="DOCX bloqueado por risco de descompressao excessiva",
                )
    except HTTPException:
        raise
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Arquivo DOCX invalido ou corrompido",
        ) from exc


def validate_file_signature(
    filename: str,
    header: bytes,
    file_path: Optional[str] = None,
) -> str:
    """Check extension, signature and container structure."""
    file_ext = validate_filename(filename)
    detected_mime = _detect_mime(header)

    if LIBMAGIC_AVAILABLE and magic is not None and header:
        try:
            libmagic_mime = magic.Magic(mime=True).from_buffer(header)
            detected_mime = MIME_ALIASES.get(libmagic_mime, libmagic_mime)
        except Exception:
            pass

    if file_ext == ".docx":
        if not header.startswith(b"PK\x03\x04") or not file_path:
            raise HTTPException(
                status_code=400,
                detail="Conteudo do arquivo nao corresponde a um DOCX valido",
            )
        _validate_docx_archive(file_path)
        return ALLOWED_TYPES[file_ext][0]

    required_signatures = {
        ".pdf": b"%PDF",
        ".png": b"\x89PNG",
        ".jpg": b"\xff\xd8\xff",
        ".jpeg": b"\xff\xd8\xff",
    }
    required = required_signatures.get(file_ext)
    if required and not header.startswith(required):
        raise HTTPException(
            status_code=400,
            detail=f"Conteudo do arquivo nao corresponde a extensao {file_ext}",
        )
    if file_ext in {".tif", ".tiff"} and not (
        header.startswith(b"\x49\x49\x2a\x00")
        or header.startswith(b"\x4d\x4d\x00\x2a")
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Conteudo do arquivo nao corresponde a extensao {file_ext}",
        )
    if file_ext == ".rtf" and not header.lstrip().startswith(b"{\\rtf"):
        raise HTTPException(
            status_code=400,
            detail="Conteudo do arquivo nao corresponde a um RTF valido",
        )
    if file_ext == ".txt" and (b"\x00" in header or header.startswith(b"MZ")):
        raise HTTPException(
            status_code=400,
            detail="Arquivo TXT contem conteudo binario ou executavel",
        )

    allowed_mimes = ALLOWED_TYPES[file_ext]
    normalized_mime = MIME_ALIASES.get(detected_mime or "", detected_mime)
    if normalized_mime and normalized_mime not in allowed_mimes:
        if not (file_ext == ".txt" and normalized_mime.startswith("text/")):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Conteudo do arquivo ({normalized_mime}) nao corresponde "
                    f"a extensao {file_ext}"
                ),
            )
    return allowed_mimes[0]


async def validate_upload(file: UploadFile, max_size_mb: int = 50) -> dict:
    """Compatibility validator that never reads beyond the configured limit."""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    file_ext = validate_filename(file.filename)
    max_size_bytes = max_size_mb * 1024 * 1024
    content = await file.read(max_size_bytes + 1)
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Maximo: {max_size_mb}MB",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    temporary_path = None
    if file_ext == ".docx":
        with NamedTemporaryFile(delete=False, suffix=file_ext) as temporary:
            temporary.write(content)
            temporary_path = temporary.name
    try:
        detected_mime = validate_file_signature(
            file.filename,
            content[:8192],
            temporary_path,
        )
    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)

    await file.seek(0)
    return {
        "valid": True,
        "mime_type": detected_mime,
        "safe_filename": f"{uuid.uuid4()}{file_ext}",
        "original_filename": file.filename,
        "content": content,
        "size": len(content),
    }


def sanitize_filename(filename: str) -> str:
    """Remove path components and unsafe characters from a display filename."""
    basename = os.path.basename((filename or "").replace("\\", "/"))
    sanitized = re.sub(r"[^\w\.-]", "_", basename)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[: 255 - len(ext)] + ext
    return sanitized or "documento"
