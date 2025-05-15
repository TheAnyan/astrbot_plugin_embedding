
# EmbeddingAdapter 用于适配各种模型提供商

[![License](https://img.shields.io/badge/License-AGPL%20v3-orange.svg)](https://opensource.org/licenses/AGPL-3.0) [![AstrBot](https://img.shields.io/badge/AstrBot-3.5%2B-blue.svg)](https://github.com/Soulter/AstrBot) ![Version](https://img.shields.io/badge/Version-1.0-success) [![GitHub](https://img.shields.io/badge/author-AnYan-blue)](https://github.com/TheAnyan)

[![Moe Counter](https://count.getloli.com/@embeddingAdapter?name=cembeddingAdapter&theme=nixietube-1&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)](https://github.com/TheAnyan/astrbot_plugin_embedding_adapter)


用于对各种embedding服务提供商进行适配。

喜欢的话点个🌟吧！



## ⚙️ 部署准备
### 插件安装
astrbot插件市场搜索astrbot_plugin_embedding_adapter，点击安装，等待完成即可。


### embedding 模型部署

#### 在线Ollama服务部署（百度）

请参考百度[鉴权方式文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Dlkm79mnx#%E5%9F%BA%E4%BA%8E%E5%AE%89%E5%85%A8%E8%AE%A4%E8%AF%81aksk%E7%AD%BE%E5%90%8D%E8%AE%A1%E7%AE%97%E8%AE%A4%E8%AF%81)

通过[创建应用](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application/v1)获取api_key和secret_key

> [!NOTE]
> 
> 请使用v1版本接口，如果在v2版本，请点击切换至旧版
> 
> 创建应用时请勾选你需要的模型，模型信息可以参考[百度千帆向量Embeddings](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/alj562vvu)

**embedding配置**

请在astrbot面板配置，插件管理 -> astrbot_plugin_cyber_archaeology -> 操作 -> 插件配置

进行五项配置：
1. 调用embedding的provider (whichprovider)
2. 在线api服务地址 (api_url)
3. api_key
4. secret_key
5. Embedding模型名称 (embed_model)


#### 在线Ollama服务部署（openai）
> [!NOTE]
> 
> 由于作者没有办法访问openai，因此没有测试。


**embedding配置**

请在astrbot面板配置，插件管理 -> astrbot_plugin_cyber_archaeology -> 操作 -> 插件配置

进行四项配置：
1. 调用embedding的provider (whichprovider)
2. 在线api服务地址 (api_url)
3. api_key
4. Embedding模型名称 (embed_model)四项




#### 本地Ollama服务部署（推荐）

通过docker部署Ollama

```yaml
version: '3.5'
services:
  ollama:
    restart: always
    container_name: 11434-ollama
    image: ollama/ollama
    ports:
      - 11434:11434
    environment:
      - OLLAMA_MODELS=/data/models
    volumes:
      - /your/path/to/models/:/data/models #你保存模型的位置，需要自己修改
    # 命令启动 serve
    command: serve
```

**下载embedding模型**

```bash
ollama pull your_model
```


| 推荐模型                       | 功能描述                             | 大小     |
|----------------------------|----------------------------------|--------|
| nomic-embed-text        | 仅英文，Ollama排名第一                   | 274 MB |
| quentinz/bge-small-zh-v1.5 | 针对中文优化的轻量级文本嵌入模型                 | 48 MB  |
| bge-m3                  | 多语言（支持100+语言）、多粒度模型，支持密集/稀疏/多向量检索 | 1.2 GB |



## 🔌 接口信息

### 核心接口方法

| 方法名 | 参数 | 返回值 | 功能描述 |
|-------|------|-------|---------|
| `get_embedding(text)` | `str` | `List[float]` | 获取当前文本的embedding向量 |
| `get_dim_async()` | 无 | `int` | 获取embedding向量的维度数 |
| `get_model_name()` | 无 | `str` | 获取当前使用的embedding模型名称 |
| `get_provider_name()` | 无 | `str` | 获取当前使用的服务商名称 |

## 插件调用方式
在AstrBot插件系统中，可以通过以下方式获取插件实例并调用方法：

```python
# 获取插件实例
embedding_adapter = context.get_registered_star("astrbot_plugin_embedding_adapter").star_cls

# 调用方法示例
embedding_vector = await embedding_adapter.get_embedding()
dimension = await embedding_adapter.get_dim_async()
model_name = embedding_adapter.get_model_name()
provider_name = embedding_adapter.get_provider_name()
```

## 当前支持的服务商
1. 百度千帆 (`baidu`)
   • 需要配置: `api_url`, `api_key`, `secret_key`, `embed_model`

2. OpenAI (`openai`)
   • 需要配置: `api_url`, `api_key`, `embed_model`

3. Ollama本地服务 (`ollama`)
   • 需要配置: `ollama_api_url`, `embed_model`


## 🛠️ 使用指南
### 基础命令
| 命令格式                         | 功能描述                  | 示例                 |
|------------------------------|-----------------------|--------------------|
| `/em ls`                     | 列出可以选择的提供商，检验可用性 | `/em ls`           |
| `/em select <provider_name>` | 清空所有群组记录(管理员权限)       | `/em select baidu` |



## ⚠️ 注意事项
1. 首次使用需部署embedding模型并进行相应配置


## 📜 开源协议
本项目采用 AGPLv3 协议开源，基于 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 插件体系开发。
