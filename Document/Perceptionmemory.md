# 感知记忆 (Perceptual Memory)

## 概述

`PerceptualMemory` 是 `HelloAgents` 框架中用于处理长期、多模态感知数据的记忆模块。它实现了 `BaseMemory` 接口，旨在存储和检索来自不同感官通道（如文本、图像、音频）的信息。

该模块结合了结构化存储（SQLite）和向量检索（Qdrant），支持跨模态相似性搜索和基于重要性的记忆管理。

## 核心特性

- **多模态支持**：能够处理文本、图像、音频、视频等多种类型的数据。
- **混合存储**：
  - **SQLite**：作为权威文档存储，保存元数据、原始内容和结构化标签。
  - **Qdrant**：作为向量存储，支持高效的相似性检索。
- **智能检索**：
  - 支持同模态和跨模态检索（依赖 CLIP/CLAP 模型）。
  - 采用混合评分算法，融合向量相似度、时间衰减（Recency）和重要性（Importance）。
- **懒加载编码**：
  - 文本使用 `sentence-transformers`。
  - 图像/音频尝试加载 CLIP/CLAP 模型，若不可用则降级为轻量级哈希向量或文本维度向量。
- **遗忘机制**：支持基于重要性、时间和容量的硬删除策略。

## 数据实体：Perception

`Perception` 类封装了单个感知数据的实体信息。

### 属性
- `perception_id`: 唯一标识符。
- `data`: 原始数据（任意类型）。
- `modality`: 模态类型（如 "text", "image", "audio", "video", "structured"）。
- `encoding`: 向量编码（浮点数列表）。
- `metadata`: 额外的元数据字典。
- `timestamp`: 创建时间戳。
- `data_hash`: 数据内容的 MD5 哈希值。

## 类：PerceptualMemory

### 初始化

```python
def __init__(self, config: MemoryConfig, storage_backend=None)
```

初始化时会配置以下组件：
1.  **内存缓存**：`perceptions` 字典和 `perceptual_memories` 列表。
2.  **模态索引**：`modality_index` 用于快速按模态查找。
3.  **文档存储**：初始化 `SQLiteDocumentStore`，数据库文件位于 `config.storage_path/memory.db`。
4.  **编码模型**：
    - 文本嵌入模型（默认 text-embedding-3-small 或类似）。
    - 尝试加载 `CLIP`（图像）和 `CLAP`（音频）模型。如果加载失败，会进行优雅降级（使用文本维度或哈希）。
5.  **向量存储**：初始化 `QdrantVectorStore`，为不同模态（text, image, audio）创建独立的集合。

### 核心方法

#### 1. 添加记忆 (`add`)

```python
def add(self, memory_item: MemoryItem) -> str
```
- **流程**：
    1. 校验模态是否支持。
    2. 生成感知数据的编码（向量）和哈希。
    3. 更新内存中的缓存和索引。
    4. **SQLite 入库**：存储完整的记忆项和属性（perception_id, modality, context, tags）。
    5. **Qdrant 入库**：将向量和元数据写入对应的模态集合。
- **返回**：记忆项 ID。

#### 2. 检索记忆 (`retrieve`)

```python
def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]
```
- **参数**：
    - `query`: 查询文本。
    - `limit`: 返回数量限制。
    - `target_modality`: 限制返回结果的模态。
    - `query_modality`: 查询内容的模态（默认为 text）。
- **算法流程**：
    1. **向量检索**：在 Qdrant 中搜索相似向量。
    2. **混合评分**：
       - 计算时间衰减分数：`recency_score = 1.0 / (1.0 + age_days)`
       - 基础相关性：`base_relevance = vector_score * 0.8 + recency_score * 0.2`
       - 重要性权重：`importance_weight = 0.8 + (importance * 0.4)`
       - 最终得分：`combined = base_relevance * importance_weight`
    3. **结果融合**：结合 SQLite 中的详细信息构建返回的 `MemoryItem`，并包含 `relevance_score`, `vector_score`, `recency_score` 等元数据。
    4. **兜底策略**：如果向量检索无结果，回退到基于关键词和模态过滤的简单匹配。

#### 3. 更新记忆 (`update`)

```python
def update(self, memory_id: str, content: str = None, importance: float = None, metadata: Dict[str, Any] = None) -> bool
```
- 同时更新内存缓存、SQLite 记录和 Qdrant 向量库中的元数据/向量。
- 如果 `content` 或 `raw_data` 发生变化，会重新计算感知数据的嵌入向量并更新到向量库。

#### 4. 删除记忆 (`remove`)

```python
def remove(self, memory_id: str) -> bool
```
- 从内存、SQLite 和 Qdrant 中彻底删除指定 ID 的记忆。
- 清理相关的模态索引和感知数据对象。

#### 5. 遗忘机制 (`forget`)

```python
def forget(self, strategy: str = "importance_based", threshold: float = 0.1, max_age_days: int = 30) -> int
```
支持三种策略：
- **importance_based**：删除重要性低于 `threshold` 的记忆。
- **time_based**：删除早于 `max_age_days` 的记忆。
- **capacity_based**：如果超出 `config.max_capacity` 容量限制，优先删除重要性低的记忆。

该方法执行**硬删除**操作，并返回被遗忘的记忆数量。

#### 6. 其他辅助方法

- `clear()`: 清空所有数据（内存、SQLite、Qdrant）。
- `get_all()`: 获取所有记忆项副本。
- `get_stats()`: 返回统计信息（活跃数量、模态计数、向量库/文档库状态）。
- `cross_modal_search()`: `retrieve` 的封装，便于语义调用。
- `get_by_modality()`: 获取指定模态的所有记忆。

## 依赖库

- `transformers`: 用于 CLIP/CLAP 模型加载（可选，若无则降级）。
- `qdrant-client`: 向量数据库客户端。
- `sqlite3`: 内置数据库。
- `hashlib`: 用于数据哈希计算。
