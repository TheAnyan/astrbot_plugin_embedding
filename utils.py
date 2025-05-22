from typing import List, Optional, Dict, Any
import re



def clean(s: str) -> str:
    # 保留字母，去除数字、标点、空格等
    return re.sub(r'[^a-zA-Z\u4e00-\u9fa5]', '', s.lower())

def str_similarity(a: str, b: str) -> float:
    """
    计算两个字符串的Jaccard相似度，不考虑数字、标点和空格等特殊符号
    """
    a_clean = clean(a)
    b_clean = clean(b)
    set_a = set(a_clean)
    set_b = set(b_clean)
    return len(set_a & set_b) / len(set_a | set_b) if set_a | set_b else 0.0

def vec_similarity(a:List[float], b:List[float]) -> float:
    """
    计算两个向量的余弦相似度
    """
    if len(a) != len(b):
        raise ValueError("Vectors must be of the same length")
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(y ** 2 for y in b) ** 0.5
    return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0