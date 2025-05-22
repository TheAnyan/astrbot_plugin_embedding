from typing import List, Optional, Dict, Any
import asyncio
import time

from astrbot.api import logger

from .utils import *
from .embedding_providers import Provider

class ModelGroupProvider:
    """
    聚合所有test_embedding一致的provider，暴露EmbeddingAdapter所有接口
    """
    def __init__(self, name:str, providers: List[Provider],default_provider_index:int=0):
        self.name=name
        if not providers:
            raise ValueError("ModelGroupProvider初始化时providers不能为空")
        self.providers = providers
        self.test_embedding = providers[0].get_test_embedding()
        self._embedding_cache = {}
        
        
        # 缓存命中机制参数
        self._cache_expire = 20  # 秒
        self.epsilon = 1e-6
        self.str_threshold = 0.9
        # 负载均衡参数
        self.default_provider_index = default_provider_index
        self.balance_threshold = 10
        self.batch_size = 8
        self.try_count_limit = 10

    def add_provider(self, provider:Provider):
        """
        添加provider
        :param provider: provider对象
        :return:
        """
        if not hasattr(provider, "get_test_embedding"):
            raise ValueError("provider必须实现get_test_embedding方法")
        try:
            logger.info(f"添加provider: {provider.get_provider_name()}到{self.name}，相似度为{vec_similarity(self.test_embedding ,provider.get_test_embedding())}")
            if vec_similarity(self.test_embedding ,provider.get_test_embedding())>1-self.epsilon:
                self.providers.append(provider)
                return True
            else:
                return False
        except ValueError as e:
            return False
        
    def set_default_provider(self, index:int):
        """
        设置默认provider
        :param index: provider索引
        :return:
        """
        if index < 0 or index >= len(self.providers):
            raise ValueError("provider索引越界")
        self.default_provider_index = index

    def _get_from_cache(self, text: str):
        for k, (ts, v) in self._embedding_cache.items():
            if str_similarity(k, text) > self.str_threshold:
                # 如果缓存的文本和当前文本相似度大于0.9，则返回缓存的值
                logger.info(f"从缓存中获取embedding: {k} -> {text}")
                return v
        return None

    def _set_cache(self, text: str, value):
        self._embedding_cache[text] = (time.time(), value)

    def _cleanup_cache(self):
        now = time.time()
        expired_cache = [k for k, (ts, _) in self._embedding_cache.items() if now - ts >= self._cache_expire]
        for k in expired_cache:
            del self._embedding_cache[k]



    def get_embedding(self, text: str):
        self._cleanup_cache()
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached

        result = self.providers[self.default_provider_index].get_embedding(text)
        self._set_cache(text, result)
        return result

    def get_embeddings(self, texts: List[str]):
        self._cleanup_cache()
        unique_texts = list(dict.fromkeys(texts))
        cache_map = {}
        uncached_texts = []
        for t in unique_texts:
            cached = self._get_from_cache(t)
            if cached is not None:
                cache_map[t] = cached
            else:
                uncached_texts.append(t)
        if uncached_texts:
            results = self.providers[self.default_provider_index].get_embeddings(uncached_texts)
            for t, r in zip(uncached_texts, results):
                self._set_cache(t, r)
                cache_map[t] = r
        return [cache_map[t] for t in texts]

    def get_dim(self):
        return self.providers[0].get_dim()

    def get_model_name(self):
        return self.name

    def get_provider_name(self):
        # 返回所有provider名拼接
        return self.providers[self.default_provider_index].get_provider_name()

    def is_available(self):
        return all(p.is_available() for p in self.providers)

    async def get_embedding_async(self, text: str):
        self._cleanup_cache()
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached
        result = await self.providers[self.default_provider_index].get_embedding_async(text)
        self._set_cache(text, result)
        return result

    async def get_embeddings_async(self, texts: List[str]):
        self._cleanup_cache()
        unique_texts = list(dict.fromkeys(texts))
        cache_map = {}
        uncached_texts = []
        for t in unique_texts:
            cached = self._get_from_cache(t)
            if cached is not None:
                cache_map[t] = cached
            else:
                uncached_texts.append(t)
        if uncached_texts:
            if len(uncached_texts) < self.balance_threshold:
                # 如果未缓存的文本数量小于平衡阈值，则使用第一个provider
                results = await self.providers[self.default_provider_index].get_embeddings_async(uncached_texts)
                for t, r in zip(uncached_texts, results):
                    self._set_cache(t, r)
                    cache_map[t] = r
            else:
                # 分批分配任务给不同provider，动态调度，每个子任务的texts数目为self.batch_size
                provider_count = len(self.providers)
                provider_available = list(range(provider_count))  # 记录每个provider的占用情况
                timeouts = 10  # 每个任务超时时间（秒）
                provider_avg_time = [1.0] * provider_count # 初始化每个provider的平均响应时间

                # 将uncached_texts分批，每批大小为self.batch_size
                batches = [uncached_texts[i:i+self.batch_size] for i in range(0, len(uncached_texts), self.batch_size)]
                batch_indices = [list(range(i, min(i+self.batch_size, len(uncached_texts)))) for i in range(0, len(uncached_texts), self.batch_size)]

                logger.info(f"测试: {provider_available}")
                async def run_batch(batch, indices):
                    nonlocal provider_avg_time
                    nonlocal provider_available
                    try_count = 0
                    while True:
                        while not provider_available:
                            # 如果所有provider都在忙，则等待
                            await asyncio.sleep(0.1)
                        if try_count > self.try_count_limit:
                            raise RuntimeError("多次调用失败，终止查询")
                        try_count += 1
                        # 选择平均响应时间最短的provider
                        provider_idx = min(provider_available, key=lambda i: provider_avg_time[i])
                        provider_available.remove(provider_idx)  # 标记为占用
                        # 选择provider_idx
                        provider = self.providers[provider_idx]
                        logger.info(f"使用provider {provider.get_provider_name()}")
                        start = time.time()
                        try:
                            r = await asyncio.wait_for(provider.get_embeddings_async(batch), timeout=timeouts)
                            elapsed = time.time() - start
                            # 更新平均响应时间（滑动平均）
                            provider_avg_time[provider_idx] = 0.7 * provider_avg_time[provider_idx] + 0.3 * elapsed
                            provider_available.append(provider_idx)  # 释放占用
                            return r, indices
                        except Exception:
                            provider_avg_time[provider_idx] += 2  # 出错惩罚
                            provider_available.append(provider_idx)
                            logger.error(f"provider {provider.get_provider_name()} 处理文本失败: {batch}")
                            raise

                tasks = [asyncio.create_task(run_batch(batch, idxs)) for batch, idxs in zip(batches, batch_indices)]
                finished = await asyncio.gather(*tasks)
                for r, idxs in finished:
                    for i, t_idx in enumerate(idxs):
                        t = uncached_texts[t_idx]
                        self._set_cache(t, r[i])
                        cache_map[t] = r[i]
        return [cache_map[t] for t in texts]

    async def get_dim_async(self):
        return await self.providers[0].get_dim_async()

    async def is_available_async(self):
        results = await asyncio.gather(*[p.is_available_async() for p in self.providers])
        return all(results)
