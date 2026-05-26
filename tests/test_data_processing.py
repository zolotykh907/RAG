import pytest
import pandas as pd
from unittest.mock import MagicMock
import pymorphy2

from rag_system.indexing.data_processing import normalize_text, compute_text_hash, check_data_quality


morph = pymorphy2.MorphAnalyzer()

@pytest.mark.parametrize("input_text, expected_tokens", [
    ("Привет, МИР!", {"привет", "мир"}),
    ("  Тестирование текста... ", {"тестирование", "текст"}),
    ("12345 ???", set()),
])


def test_normalize_text(input_text, expected_tokens):
    """Verify text normalization with lemmatization.

    Args:
        input_text: Raw text from the parametrized case.
        expected_tokens: Expected normalized tokens.
    """
    result = normalize_text(input_text, morph=morph, clear_flag=True)
    result_tokens = set(result.split())
    assert result_tokens == expected_tokens


def test_compute_text_hash_consistency():
    """Verify equivalent normalized texts produce the same hash."""
    text = "Пример текста"
    hash1 = compute_text_hash(text)
    hash2 = compute_text_hash(" пример ТЕКСТА  ")
    assert hash1 == hash2


def test_compute_text_hash_different():
    """Verify different texts produce different hashes."""
    assert compute_text_hash("abc") != compute_text_hash("def")


def test_check_data_quality():
    """Verify quality checks remove empty, short, and duplicate texts."""
    data = {
        'uid': ['1', '2', '3', '4', '5'],
        'text': [
            'Привет мир!',         # len 11
            ' ',                   # empty
            'Кратко',              # len 6
            'Привет мир!',         # duplicate
            'Что-то интересное'    # len 17
        ]
    }
    df = pd.DataFrame(data)
    logger = MagicMock()

    report, df_clean = check_data_quality(df, logger, min_len=10)

    assert report['empty_docs']['count'] == 1
    assert report['short_texts']['count'] == 1
    assert report['duplicate_texts']['count'] == 1

    assert len(df_clean) == 2
    assert list(df_clean['uid']) == ['1', '5']
    assert all(df_clean['text'].str.strip().str.len() >= 10)
