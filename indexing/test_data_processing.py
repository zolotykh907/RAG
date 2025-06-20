import pytest
from data_processing import normalize_text, compute_text_hash, check_data_quality
import pandas as pd
from unittest.mock import MagicMock

# --------- Тест normalize_text ---------

@pytest.mark.parametrize("input_text, expected_tokens", [
    ("Привет, МИР!", {"привет", "мир"}),
    ("  Тестирование текста... ", {"тестирование", "текст"}),
    ("12345 ???", set()),
])
def test_normalize_text(input_text, expected_tokens):
    result = normalize_text(input_text)
    result_tokens = set(result.split())
    assert result_tokens == expected_tokens

# --------- Тест compute_text_hash ---------

def test_compute_text_hash_consistency():
    text = "Пример текста"
    hash1 = compute_text_hash(text)
    hash2 = compute_text_hash(" пример ТЕКСТА  ")
    assert hash1 == hash2  # одинаковый текст после нормализации => одинаковый хеш

def test_compute_text_hash_different():
    assert compute_text_hash("abc") != compute_text_hash("def")


def test_check_data_quality():
    data = {
        'uid': ['1', '2', '3', '4', '5'],
        'text': [
            'Привет мир!',         # длина 11
            ' ',                   # пустой (пробел)
            'Кратко',              # длина 6
            'Привет мир!',         # дубликат
            'Что-то интересное'    # длина 17
        ]
    }
    df = pd.DataFrame(data)
    logger = MagicMock()

    report, df_clean = check_data_quality(df, logger, min_len=10)

    # Проверяем отчёт
    assert report['empty_docs']['count'] == 1  # ' '
    assert report['short_texts']['count'] == 1 # 'Кратко'
    assert report['duplicate_texts']['count'] == 2 # один дубликат (второе 'Привет мир!')

    # Проверяем очищенные данные (должны остаться только строки 0 и 4)
    assert len(df_clean) == 2
    assert list(df_clean['uid']) == ['1', '5']  # проверяем оставшиеся uid
    assert all(df_clean['text'].str.strip().str.len() >= 10)  # ключевое исправление!