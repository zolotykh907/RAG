from pathlib import Path

import pytesseract
from PIL import Image
from pdf2image import convert_from_path


class OCR:
    def __init__(self):
        self.image_types = ('.jpg', '.jpeg', '.png')


    def rotate_image(self, img):
        osd = pytesseract.image_to_osd(img, output_type='dict')
        angle = osd['orientation']

        return img.rotate(angle)


    def load_pages(self, path, dpi=150):
        path = Path(path)

        if not path.is_dir():
            return []

        for file in path.iterdir():
            if file.suffix.lower() == '.pdf':
                try:
                    yield from convert_from_path(file, dpi=dpi)
                except Exception as e:
                    print(f"Ошибка при обработке PDF {file}: {e}")
            elif file.suffix.lower() in self.image_types:
                try:
                    yield Image.open(file)
                except Exception as e:
                    print(f"Ошибка при открытии изображения {file}: {e}")


    def get_text_from_image(self, img):
        img = self.rotate_image(img)
        text = pytesseract.image_to_string(image=img, lang='rus+eng')

        return text
    

    def run_ocr(self, path):
        texts = []
        for page in self.load_pages(path):
            text = self.get_text_from_image(page)
            texts.append(text)

        return texts