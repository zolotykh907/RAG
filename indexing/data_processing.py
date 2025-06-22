import re
import hashlib
import logging
from tqdm import tqdm


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataProcessing")


def normalize_text(text, morph):
    """Normalize text.
    
    Args:
        text (str): input text for processing.
        morph (MorphAnalizer): Morphological analyzer.

    Returns:
        str: normalized text
    """
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)

    words = text.split()
    lemmas = [morph.parse(word)[0].normal_form for word in words if word.isalpha()]
    
    res = ' '.join(lemmas)

    return res


def compute_text_hash(text):
    """Compute sha256 hash for input text.

    Args:
        text (str): input text for hashing.

    Returns:
        str: sha256 hash for input text
    """
    return hashlib.sha256(text.strip().lower().encode('utf-8')).hexdigest()


def check_data_quality(df, min_len=10):
    """Check data quality.

    Args:
        df (DataFrame): input DataFrame with texts and uids.
        min_len (int, optional): Min text length threshold.

    Returns:
        tuple: dict with quality check results and clean DataFrame
    """

    df = df.copy()
    df['text'] = df['text'].str.strip()

    # Empty docs
    empty_docs = df[(df['text'] == '')]
    logger.info(f'Пустых документов: {len(empty_docs)}')

    # Duplicates uids
    duplicate_uids = df[df.duplicated(subset=['uid'], keep=False)]
    logger.info(f"Дубликатов по uid: {len(duplicate_uids)}")

    # Duplicates texts
    df['text_hash'] = df['text'].apply(compute_text_hash)
    duplicate_texts = df[df.duplicated(subset=['text_hash'], keep=False)]
    logger.info(f"Дубликатов текстов: {len(duplicate_texts)}")

    # Short texts
    short_texts = df[(df['text'].str.len() < min_len) & (df['text'] != '')]
    logger.info(f'Текстов длиной меньше {min_len}: {len(short_texts)}')

    # Results
    res = {}
    res['empty_docs'] = {'count': len(empty_docs), 
                         'data': empty_docs.to_dict(orient='records')}
    res['duplicate_uids'] = {'count': len(duplicate_uids), 
                             'data': duplicate_uids.to_dict(orient='records')}
    res['duplicate_texts'] = {'count': len(duplicate_texts), 
                              'data': duplicate_texts.to_dict(orient='records')}
    res['short_texts'] = {'count': len(short_texts), 
                          'data': short_texts.to_dict(orient='records')}

    # Cleaning df
    df_clean = df[
        (df['text'] != '') & 
        (df['text'].str.len() >= min_len)  
    ].drop_duplicates(subset=['text_hash'], keep='first')
    
    return res, df_clean