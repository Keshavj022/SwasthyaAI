"""
File Storage Service - Local disk storage for medical documents and images.

Handles:
- Secure file uploads
- Organized directory structure
- Metadata extraction
- File validation
- Storage path management

All files stored locally in database/documents/ directory.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import magic  # python-magic for file type detection
import logging

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    Manages local file storage for medical documents.
    """

    # Base storage directory
    BASE_STORAGE_DIR = Path(__file__).parent.parent.parent / "database" / "documents"

    # Document type subdirectories
    DOCUMENT_TYPES = {
        "xray": "xrays",
        "ct_scan": "ct_scans",
        "mri": "mri_scans",
        "ultrasound": "ultrasounds",
        "lab_report": "lab_reports",
        "prescription": "prescriptions",
        "insurance_card": "insurance",
        "consent_form": "consent_forms",
        "discharge_summary": "discharge_summaries",
        "other": "other"
    }

    # Allowed file extensions and MIME types
    ALLOWED_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",  # Images
        ".pdf",  # PDFs
        ".dcm",  # DICOM medical imaging
        ".doc", ".docx",  # Word documents
        ".txt"  # Text files
    }

    ALLOWED_MIME_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff",
        "application/pdf",
        "application/dicom",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }

    # Max file size (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self):
        """Initialize file storage service and ensure base directory exists"""
        self.BASE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"File storage initialized at: {self.BASE_STORAGE_DIR}")

    def save_file(
        self,
        file_content: bytes,
        file_name: str,
        patient_id: str,
        document_type: str = "other"
    ) -> Dict[str, Any]:
        """
        Save file to local storage with organized directory structure.

        Args:
            file_content: Binary file content
            file_name: Original file name
            patient_id: Patient identifier
            document_type: Type of document (xray, lab_report, etc.)

        Returns:
            Dict with file_path, file_size, mime_type, metadata

        Raises:
            ValueError: If file validation fails
        """
        # Validate file
        self._validate_file(file_content, file_name)

        # Get file extension
        file_ext = Path(file_name).suffix.lower()

        # Detect MIME type
        mime_type = self._detect_mime_type(file_content, file_ext)

        # Generate unique filename (hash + timestamp)
        unique_filename = self._generate_unique_filename(file_name, file_content)

        # Build storage path
        storage_path = self._build_storage_path(
            patient_id,
            document_type,
            unique_filename
        )

        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        storage_path.write_bytes(file_content)

        logger.info(f"Saved file: {storage_path} ({len(file_content)} bytes)")

        # Extract metadata
        metadata = self._extract_metadata(file_content, file_name, mime_type)

        return {
            "file_path": str(storage_path.relative_to(self.BASE_STORAGE_DIR.parent)),
            "file_name": unique_filename,
            "original_name": file_name,
            "file_size": len(file_content),
            "mime_type": mime_type,
            "metadata": metadata
        }

    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve file content from storage.

        Args:
            file_path: Relative path to file (from database record)

        Returns:
            File content bytes or None if not found
        """
        # Convert relative path to absolute
        full_path = self.BASE_STORAGE_DIR.parent / file_path

        if not full_path.exists():
            logger.error(f"File not found: {full_path}")
            return None

        # Security check: ensure path is within storage directory
        if not str(full_path.resolve()).startswith(str(self.BASE_STORAGE_DIR.parent.resolve())):
            logger.error(f"Security violation: Path outside storage directory: {full_path}")
            return None

        return full_path.read_bytes()

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Relative path to file

        Returns:
            True if deleted, False if not found
        """
        full_path = self.BASE_STORAGE_DIR.parent / file_path

        if not full_path.exists():
            return False

        # Security check
        if not str(full_path.resolve()).startswith(str(self.BASE_STORAGE_DIR.parent.resolve())):
            logger.error(f"Security violation: Path outside storage directory: {full_path}")
            return False

        full_path.unlink()
        logger.info(f"Deleted file: {full_path}")

        # Clean up empty directories
        self._cleanup_empty_dirs(full_path.parent)

        return True

    def _validate_file(self, file_content: bytes, file_name: str):
        """
        Validate file size and extension.

        Raises:
            ValueError: If validation fails
        """
        # Check file size
        if len(file_content) == 0:
            raise ValueError("File is empty")

        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(file_content)} bytes "
                f"(max: {self.MAX_FILE_SIZE} bytes / {self.MAX_FILE_SIZE // (1024*1024)} MB)"
            )

        # Check extension
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File type not allowed: {file_ext}. "
                f"Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

    def _detect_mime_type(self, file_content: bytes, file_ext: str) -> str:
        """
        Detect MIME type from file content using magic bytes.

        Args:
            file_content: Binary file content
            file_ext: File extension

        Returns:
            MIME type string
        """
        try:
            # Try to detect using magic (more reliable)
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_buffer(file_content)

            # Validate detected MIME type is allowed
            if detected_mime in self.ALLOWED_MIME_TYPES:
                return detected_mime

        except Exception as e:
            logger.warning(f"Could not detect MIME type with magic: {str(e)}")

        # Fallback to extension-based detection
        mime_type, _ = mimetypes.guess_type(f"file{file_ext}")
        return mime_type or "application/octet-stream"

    def _generate_unique_filename(self, original_name: str, file_content: bytes) -> str:
        """
        Generate unique filename using hash + timestamp.

        Args:
            original_name: Original filename
            file_content: File content for hashing

        Returns:
            Unique filename
        """
        # Hash first 1KB of file content for uniqueness
        file_hash = hashlib.sha256(file_content[:1024]).hexdigest()[:12]

        # Timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Extension
        file_ext = Path(original_name).suffix.lower()

        return f"{timestamp}_{file_hash}{file_ext}"

    def _build_storage_path(
        self,
        patient_id: str,
        document_type: str,
        filename: str
    ) -> Path:
        """
        Build organized storage path.

        Structure:
        database/documents/patient_{patient_id}/{document_type_dir}/{filename}

        Args:
            patient_id: Patient identifier
            document_type: Document type
            filename: Unique filename

        Returns:
            Full storage path
        """
        # Get document type subdirectory
        type_dir = self.DOCUMENT_TYPES.get(document_type, "other")

        # Build path
        return self.BASE_STORAGE_DIR / f"patient_{patient_id}" / type_dir / filename

    def _extract_metadata(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from file.

        Future enhancements:
        - PDF text extraction
        - DICOM metadata extraction
        - Image EXIF data
        - OCR for scanned documents

        Args:
            file_content: Binary file content
            file_name: Filename
            mime_type: MIME type

        Returns:
            Dict with metadata
        """
        metadata = {
            "original_filename": file_name,
            "mime_type": mime_type,
            "size_bytes": len(file_content)
        }

        # Image metadata
        if mime_type.startswith("image/"):
            metadata["type"] = "image"
            # Future: Extract EXIF data, dimensions

        # PDF metadata
        elif mime_type == "application/pdf":
            metadata["type"] = "pdf"
            # Future: Extract page count, text content

        # DICOM metadata
        elif mime_type == "application/dicom":
            metadata["type"] = "dicom"
            # Future: Extract patient info, modality, study date

        return metadata

    def _cleanup_empty_dirs(self, directory: Path):
        """
        Remove empty directories up the tree.

        Args:
            directory: Directory to start from
        """
        try:
            while directory != self.BASE_STORAGE_DIR and directory.exists():
                if not any(directory.iterdir()):
                    directory.rmdir()
                    logger.debug(f"Removed empty directory: {directory}")
                    directory = directory.parent
                else:
                    break
        except Exception as e:
            logger.warning(f"Could not cleanup directory {directory}: {str(e)}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict with total files, total size, etc.
        """
        total_files = 0
        total_size = 0

        for file_path in self.BASE_STORAGE_DIR.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.BASE_STORAGE_DIR)
        }


# Global singleton instance
file_storage = FileStorageService()
