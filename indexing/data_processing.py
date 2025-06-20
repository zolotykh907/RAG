import re
import hashlib
import logging
import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def normalize_text(text):
    text = text.strip()
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)

    words = text.split()
    lemmas = [morph.parse(word)[0].normal_form for word in words if word.isalpha()]
    
    return ' '.join(lemmas)


def compute_text_hash(text):
    return hashlib.sha256(text.strip().lower().encode('utf-8')).hexdigest()


def check_data_quality(df, logger, min_len=10):
    # Удаление лишних пробелов
    df['text'] = df['text'].str.strip()

    # Проверка на пустые документы
    empty_docs = df[(df['text'].str.strip() == '')]
    logger.info(f'Пустых документов: {len(empty_docs)}')

    # Проверка дубликатов
    duplicate_uids = df[df.duplicated(subset=['uid'], keep=False)]
    logger.info(f"Дубликатов по uid: {len(duplicate_uids)}")

    df['text_hash'] = df['text'].apply(compute_text_hash)
    duplicate_texts = df[df.duplicated(subset=['text_hash'], keep=False)]
    logger.info(f"Дубликатов текстов: {len(duplicate_texts)}")

    # Проверка на минимальную длину
    short_texts = df[df['text'].str.len() < min_len]
    logger.info(f'Текстов длиной меньше {min_len}: {len(short_texts)}')

    res = {}
    res['empty_docs'] = {'count': len(empty_docs), 'data': empty_docs.to_dict(orient='records')}
    res['duplicate_uids'] = {'count': len(duplicate_uids), 'data': duplicate_uids.to_dict(orient='records')}
    res['duplicate_texts'] = {'count': len(duplicate_texts), 'data': duplicate_texts.to_dict(orient='records')}
    res['short_texts'] = {'count': len(short_texts), 'data': short_texts.to_dict(orient='records')}

    # Очистка данных
    short_texts_uids = short_texts['uid']
    df_clean = df[~df['uid'].isin(short_texts_uids)]

    df_clean = df_clean.drop_duplicates(subset=['text_hash'], keep='first')
    #df_clean = df_clean.drop('text_hash', axis=1)
    
    return res, df_clean