from pathlib import Path
from typing import Any, Generator, List, Union

import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from rag_system.shared.logs import setup_logging


class OCR:
    """Extract text from supported image and PDF files with Tesseract OCR."""

    def __init__(self, config: Any) -> None:
        self.logs_dir: str = config.logs_dir
        self.logger = setup_logging(self.logs_dir, 'OCRsystem')
        self.image_types: tuple = config.image_types
        self.doc_types: tuple = config.doc_types

    def rotate_image(self, img: Image.Image) -> Image.Image:
        """Rotate an image according to OCR orientation metadata.

        Args:
            img: PIL image to inspect and rotate.

        Returns:
            The rotated image, or the original image if orientation detection fails.
        """
        try:
            osd = pytesseract.image_to_osd(img, output_type='dict')
            angle = osd['orientation']
            return img.rotate(angle)
        except Exception as e:
            self.logger.info(f"Error determining orientation: {e}")
            return img

    def get_text_from_image(self, img: Image.Image) -> str:
        """Extract Russian and English text from one image.

        Args:
            img: PIL image to process.

        Returns:
            Text recognized by Tesseract.
        """
        img = self.rotate_image(img)
        text: str = pytesseract.image_to_string(image=img, lang='rus+eng')
        return text

    def load_pages(self, path: Union[str, Path], dpi: int = 150) -> Generator[Image.Image, None, None]:
        """Yield images from a PDF, image file, or directory.

        Args:
            path: File or directory path to process.
            dpi: PDF rendering resolution.

        Returns:
            A generator of PIL images ready for OCR.
        """
        path = Path(path)

        if path.suffix.lower() == '.pdf':
            try:
                pages = convert_from_path(path, dpi=dpi)
                self.logger.info(f"Found {len(pages)} pages in PDF")
                yield from pages
            except Exception as e:
                self.logger.error(f"Error processing PDF {path}: {e}")
                return

        elif path.is_dir():
            for file in path.iterdir():
                if file.suffix.lower() == '.pdf':
                    try:
                        yield from convert_from_path(file, dpi=dpi)
                    except Exception as e:
                        self.logger.error(f"Error processing PDF {file}: {e}")
                elif file.suffix.lower() in self.image_types:
                    try:
                        yield Image.open(file)
                    except Exception as e:
                        self.logger.error(f"Error opening image {file}: {e}")

        elif path.suffix.lower() in self.image_types:
            try:
                yield Image.open(path)
            except Exception as e:
                self.logger.error(f"Error opening image {path}: {e}")

    def run_ocr(self, path: Union[str, Path]) -> List[str]:
        """Run OCR over all pages or images found at a path.

        Args:
            path: File or directory path to process.

        Returns:
            Recognized text for each processed page or image.
        """
        texts: List[str] = []
        try:
            for i, page in enumerate(self.load_pages(path), 1):
                self.logger.info(f"Processing page {i}")
                text = self.get_text_from_image(page)
                texts.append(text)
        except Exception as e:
            self.logger.error(f"Error in run_ocr: {e}")

        if not texts:
            self.logger.warning("No pages were processed")

        return texts
