import json
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Union

import pandas as pd

from rag_system.shared.logs import setup_logging
from rag_system.shared.ocr import OCR


class DataLoader:
    _text_file_extensions = ('.txt', '.md', '.markdown')
    _word_xml_namespace = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    _docx_text_parts = (
        'word/document.xml',
        'word/footnotes.xml',
        'word/endnotes.xml',
    )

    def __init__(self, config: Any) -> None:
        self.ocr_types: tuple = tuple(config.ocr_types)
        self.logs_dir: str = config.logs_dir
        self.logger = setup_logging(self.logs_dir, 'DataLoader')
        self.ocr = OCR(config)

    def from_json(self, path: str, column_name: str = 'text') -> pd.DataFrame:
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded data from {path}.")

            df = pd.DataFrame(data)

            if column_name not in df.columns:
                raise ValueError(f'Column "{column_name}" not found in file {path}')

            self.logger.info(f'Data from {path} loaded successfully')
            return df
        except FileNotFoundError:
            self.logger.error(f'File not found: {path}')
            raise

    def from_text_file(self, path: str) -> pd.DataFrame:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()

            df = pd.DataFrame({'text': [text]})
            return df
        except Exception:
            self.logger.info(f'Error loading data from {path}')
            raise

    def from_docx(self, path: str) -> pd.DataFrame:
        try:
            texts: List[str] = []
            with zipfile.ZipFile(path) as archive:
                for part_name in self._docx_part_names(archive):
                    xml_content = archive.read(part_name)
                    part_text = self._extract_docx_part_text(xml_content)
                    if part_text:
                        texts.append(part_text)

            return pd.DataFrame({'text': ['\n\n'.join(texts)]})
        except zipfile.BadZipFile as e:
            raise ValueError(f'Invalid DOCX file: {path}') from e
        except KeyError as e:
            raise ValueError(f'Invalid DOCX structure: {path}') from e

    def _docx_part_names(self, archive: zipfile.ZipFile) -> List[str]:
        archive_names = set(archive.namelist())
        part_names = [part for part in self._docx_text_parts if part in archive_names]
        part_names.extend(
            sorted(
                name for name in archive_names
                if name.startswith('word/header') and name.endswith('.xml')
            )
        )
        part_names.extend(
            sorted(
                name for name in archive_names
                if name.startswith('word/footer') and name.endswith('.xml')
            )
        )
        return part_names

    def _extract_docx_part_text(self, xml_content: bytes) -> str:
        root = ET.fromstring(xml_content)
        paragraph_tag = f'{self._word_xml_namespace}p'
        paragraphs: List[str] = []

        for paragraph in root.iter(paragraph_tag):
            paragraph_text = self._extract_docx_paragraph_text(paragraph).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)

        return '\n'.join(paragraphs)

    def _extract_docx_paragraph_text(self, paragraph: ET.Element) -> str:
        text_tag = f'{self._word_xml_namespace}t'
        tab_tag = f'{self._word_xml_namespace}tab'
        break_tags = {
            f'{self._word_xml_namespace}br',
            f'{self._word_xml_namespace}cr',
        }
        chunks: List[str] = []

        for node in paragraph.iter():
            if node.tag == text_tag and node.text:
                chunks.append(node.text)
            elif node.tag == tab_tag:
                chunks.append('\t')
            elif node.tag in break_tags:
                chunks.append('\n')

        return ''.join(chunks)

    def from_string(self, string: str) -> pd.DataFrame:
        df = pd.DataFrame({'text': [string]})
        return df

    def from_list(self, data_list: List[str]) -> pd.DataFrame:
        df = pd.DataFrame({'text': data_list})
        return df

    def from_pdf_or_img(self, path: str) -> pd.DataFrame:
        texts = self.ocr.run_ocr(path)
        df = pd.DataFrame({'text': texts})
        return df

    def from_dir(self, path: str) -> pd.DataFrame:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory not found: {path}")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path is not a directory: {path}")

        res_df: List[pd.DataFrame] = []

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            try:
                df = self.load_data(file_path)
                if df is not None:
                    res_df.append(df)
            except Exception as e:
                self.logger.warning(f"Error loading {file_path}: {e}")

        if not res_df:
            self.logger.warning(f"No valid files found in directory: {path}")
            return pd.DataFrame({'text': []})

        return pd.concat(res_df, ignore_index=True)

    def load_data(self, data: Union[str, List[str]]) -> pd.DataFrame:
        try:
            if isinstance(data, str):
                if os.path.isdir(data):
                    return self.from_dir(data)
                suffix = Path(data).suffix.lower()
                if suffix == '.json':
                    return self.from_json(data)
                elif suffix in self._text_file_extensions:
                    return self.from_text_file(data)
                elif suffix == '.docx':
                    return self.from_docx(data)
                elif suffix in self.ocr_types:
                    return self.from_pdf_or_img(data)
                elif os.path.exists(data):
                    raise ValueError(f"Unsupported file format: {suffix or 'no extension'}")
                else:
                    return self.from_string(data)
            elif isinstance(data, list):
                return self.from_list(data)
            raise TypeError(f"Unsupported data source type: {type(data).__name__}")
        except Exception as e:
            self.logger.error(f'Error loading data: {e}')
            raise
