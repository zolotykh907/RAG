import re
import hashlib

try:
    from logs import setup_logging  
except ImportError:
    from .logs import setup_logging  


logger = setup_logging('./logs', 'DataProcessing')

def normalize_text(text, morph=None, clear_flag = False):
    """Normalize text.
    
    Args:
        text (str): input text for processing.
        morph (MorphAnalizer): Morphological analyzer.

    Returns:
        str: normalized text.
    """
    if not isinstance(text, str):
        raise ValueError("Input text must be a string")
    
    if clear_flag:
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)

        words = text.split()
        lemmas = [morph.parse(word)[0].normal_form 
                for word in words 
                if word.isalpha()]
        
        res = ' '.join(lemmas)

        return res
    
    return text.strip()

def compute_text_hash(text):
    """Compute sha256 hash for input text.

    Args:
        text (str): input text for hashing.

    Returns:
        str: sha256 hash for input text
    """
    return hashlib.sha256(text.strip().lower().encode('utf-8')).hexdigest()


def check_data_quality(df, logger=logger, min_len=10):
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
    logger.info(f'Number of empty docs: {len(empty_docs)}')

    # Duplicates texts
    df['hash'] = df['text'].apply(compute_text_hash)
    duplicate_texts = df[df.duplicated(subset=['hash'], keep='first')]
    logger.info(f"Number of duplicates by hashes: {len(duplicate_texts)}")

    # Short texts
    short_texts = df[(df['text'].str.len() < min_len) & (df['text'] != '')]
    logger.info(f'Number of docs shorter {min_len}: {len(short_texts)}')

    # Results
    res = {}
    res['empty_docs'] = {'count': len(empty_docs), 
                         'data': empty_docs.to_dict(orient='records')}
    res['duplicate_texts'] = {'count': len(duplicate_texts), 
                              'data': duplicate_texts.to_dict(orient='records')}
    res['short_texts'] = {'count': len(short_texts), 
                          'data': short_texts.to_dict(orient='records')}

    # Cleaning df
    df_clean = df[
        (df['text'] != '') & 
        (df['text'].str.len() >= min_len)  
    ].drop_duplicates(subset=['hash'], keep='first')
    
    res['remaining_docs'] = len(df_clean)
    res['removed_docs'] = len(df) - len(df_clean)
    logger.info(f'Docs after cleaning: {len(df_clean)}')
    logger.info(f'Docs removed: {len(df) - len(df_clean)}')

    return res, df_clean