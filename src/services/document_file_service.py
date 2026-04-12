from __future__ import annotations

import mimetypes
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


from fastapi import HTTPException, UploadFile, status

PDF_MIME = "application/pdf"
SUPPORTED_CONVERTIBLE_MIME_PREFIXES = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
    "text/rtf",
}
SUPPORTED_CONVERTIBLE_EXTENSIONS = {".doc", ".docx", ".odt", ".rtf"}


async def ensure_pdf_file(upload: UploadFile) -> tuple[Path, str, str]:

    original_name = upload.filename or "document"
    content_type = (upload.content_type or "").lower()
    suffix = Path(original_name).suffix.lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source_path = tmpdir_path / original_name

        with source_path.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        # already a PDF
        if content_type == PDF_MIME or suffix == ".pdf":
            final_pdf = tmpdir_path / f"{source_path.stem}.pdf"
            shutil.copy2(source_path, final_pdf)
            persisted_pdf = Path(tempfile.mkstemp(suffix=".pdf")[1])
            shutil.copy2(final_pdf, persisted_pdf)
            return persisted_pdf, original_name, PDF_MIME

        if content_type not in SUPPORTED_CONVERTIBLE_MIME_PREFIXES and suffix not in SUPPORTED_CONVERTIBLE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only PDF, DOC, DOCX, ODT and RTF files are supported for conversion",
            )

        outdir = tmpdir_path / "out"
        profile_dir = tmpdir_path / "lo-profile"
        outdir.mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["HOME"] = str(tmpdir_path)
        env["TMPDIR"] = str(tmpdir_path)

        cmd = [
            "soffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(outdir),
            str(source_path),
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            check=False,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"LibreOffice conversion failed: {result.stderr.strip() or result.stdout.strip()}",
            )

        converted_files = list(outdir.glob("*.pdf"))
        if not converted_files:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="LibreOffice did not produce a PDF file",
            )

        persisted_pdf = Path(tempfile.mkstemp(suffix=".pdf")[1])
        shutil.copy2(converted_files[0], persisted_pdf)
        return persisted_pdf, original_name, content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"