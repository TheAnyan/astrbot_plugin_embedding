"""
provider_mapping.py
Embedding提供商映射配置
"""

from .embedding_providers import (
    OpenaiProvider,
    OllamaProvider,
    GeminiProvider
)

# 提供商名称到类的映射
PROVIDER_CLASS_MAP = {
    "openai": OpenaiProvider,
    "ollama": OllamaProvider,
    "gemini": GeminiProvider
}

# 各提供商所需的配置字段
REQUIRED_CONFIGS = {
    "openai": ["api_url", "embed_model", "api_key"],
    "ollama": ["api_url", "embed_model"],
    "gemini": ["api_key", "embed_model"]
}


def get_provider(provider_name: str, config: dict):
    """
    获取指定provider的实例
    :param provider_name: 提供商名称
    :param config: 配置字典
    :return: Provider实例
    :raises ValueError: 当配置不完整或提供商不存在时
    """
    if provider_name not in PROVIDER_CLASS_MAP:
        raise ValueError(f"不支持的embedding提供商: {provider_name}")

    required = REQUIRED_CONFIGS[provider_name]
    missing = [field for field in required if field not in config]
    if missing:
        raise ValueError(f"缺少必要配置字段: {missing}")

    return PROVIDER_CLASS_MAP[provider_name](config)