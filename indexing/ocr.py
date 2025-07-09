from pathlib import Path
import pytesseract
from PIL import Image
from pdf2image import convert_from_path


try:
    from logs import setup_logging  
except ImportError:
    from ..indexing.logs import setup_logging 

class OCR:
    def __init__(self):
        self.logger = setup_logging('./logs/', 'OCRsystem')
        self.image_types = ('.jpg', '.jpeg', '.png')

    def rotate_image(self, img):
        try:
            osd = pytesseract.image_to_osd(img, output_type='dict')
            angle = osd['orientation']
            return img.rotate(angle)
        except Exception as e:
            self.logger.info(f"Error determining orientation: {e}")
            return img

    def get_text_from_image(self, img):
        img = self.rotate_image(img)
        text = pytesseract.image_to_string(image=img, lang='rus+eng')

        return text
    
    def load_pages(self, path, dpi=150):
        path = Path(path)
        
        if path.suffix.lower() == '.pdf':
            try:
                pages = convert_from_path(path, dpi=dpi)
                self.logger.info(f"Found {len(pages)} страниц в PDF")
                yield from pages  # Изменено: используем yield from вместо return
            except Exception as e:
                self.logger.error(f"Error processing PDF {path} {path}: {e}")
                return  # Пустой генератор
        
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
                self.logger.error(f"Error opening image {path} {path}: {e}")

    def run_ocr(self, path):
        texts = []
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