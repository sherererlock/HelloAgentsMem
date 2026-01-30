# 语义记忆 (SemanticMemory)

语义记忆是 `HelloAgents` 记忆系统中最复杂且核心的部分，负责存储抽象的概念、规则和知识。它采用了混合架构，结合了向量检索（Vector Search）和知识图谱（Knowledge Graph）的优势，既能进行快速的语义相似度检索，又能利用图谱进行复杂的关系推理。

## 核心特性

- **混合检索架构**：结合 Qdrant 向量数据库和 Neo4j 图数据库。
- **智能实体提取**：集成 spaCy NLP 引擎，支持多语言（中文/英文）实体识别。
- **深度语义理解**：不仅仅存储文本，还存储文本中的实体、关系以及词法分析结果。
- **动态知识图谱**：自动构建实体间的关系网络，支持多跳推理。
- **概率评分机制**：基于向量相似度和图关联度的综合评分，并引入 Softmax 概率归一化。

## 架构设计

### 1. 数据存储层
- **Qdrant 向量数据库**：存储记忆文本的高维向量表示（Embedding），用于快速的语义相似度匹配。
- **Neo4j 图数据库**：存储实体（Entities）、关系（Relations）以及词法分析结果（Tokens, Concepts），构建知识网络。

### 2. 处理层
- **Embedding 模型**：使用 HuggingFace 预训练模型将文本转化为向量。
- **NLP 处理器**：使用 spaCy 进行分词、词性标注、依存句法分析和命名实体识别（NER）。

## 数据结构

### 实体 (Entity)
代表知识图谱中的节点。
- `entity_id`: 唯一标识符
- `name`: 实体名称
- `entity_type`: 实体类型 (如 PERSON, ORG, CONCEPT 等)
- `description`: 描述信息
- `properties`: 其他属性
- `frequency`: 出现频率

### 关系 (Relation)
代表实体之间的边。
- `from_entity`: 源实体 ID
- `to_entity`: 目标实体 ID
- `relation_type`: 关系类型
- `strength`: 关系强度 (0.0 - 1.0)
- `evidence`: 证据文本

## 核心功能详解

### 1. 初始化 (`__init__`)
初始化过程中会建立与 Qdrant 和 Neo4j 的连接，加载 Embedding 模型，并根据环境加载合适的 spaCy 语言模型（优先尝试中文 `zh_core_web_sm`，其次英文 `en_core_web_sm`）。

### 2. 添加记忆 (`add`)
当添加一条新的语义记忆时，系统执行以下步骤：
1.  **向量化**：计算记忆内容的 Embedding 向量。
2.  **实体关系提取**：
    -   使用 spaCy 提取文本中的实体。
    -   生成实体间的共现关系。
    -   (可选) 进行详细的词法分析并将 Token 存入图数据库。
3.  **图存储**：将提取的实体和关系存入 Neo4j。
4.  **向量存储**：将向量和元数据（包含实体 ID 列表）存入 Qdrant。
5.  **本地缓存**：更新本地的实体和关系缓存。

### 3. 检索记忆 (`retrieve`)
检索过程是一个多路召回与重排序的过程：
1.  **向量检索**：在 Qdrant 中搜索与查询向量最相似的记忆。
2.  **图检索**：
    -   从查询中提取实体。
    -   在 Neo4j 中查找这些实体的相关实体（支持多跳）。
    -   找到与这些实体关联的记忆。
3.  **混合排序 (`_combine_and_rank_results`)**：
    -   合并向量检索和图检索的结果。
    -   计算综合得分：`Score = (VectorScore * 0.7 + GraphScore * 0.3) * ImportanceWeight`。
    -   计算 Softmax 概率，为每个结果分配置信度。
4.  **结果过滤**：过滤掉标记为“已遗忘”的记忆，返回 Top-K 结果。

### 4. 记忆遗忘 (`forget`)
支持多种遗忘策略的硬删除机制：
-   `importance_based`: 删除重要性低于阈值的记忆。
-   `time_based`: 删除超过保留期限的记忆。
-   `capacity_based`: 当超出容量限制时，保留重要性最高的记忆。

### 5. 实体与图谱操作
-   `search_entities`: 根据名称、类型、描述搜索实体。
-   `get_related_entities`: 获取指定实体的相关实体，支持指定关系类型和跳数（Max Hops）。
-   `export_knowledge_graph`: 导出当前内存中的知识图谱统计信息。

## 辅助功能

-   **语言检测 (`_detect_language`)**：基于字符范围统计简单判断中英文，用于选择 NLP 模型。
-   **词法分析存储 (`_store_linguistic_analysis`)**：将 Token、词性 (POS)、依存关系 (Dependency) 存入 Neo4j，支持细粒度的语言学查询。

## 配置依赖

使用该模块需要正确配置 `config.yaml` 或环境变量中的数据库连接信息：
-   **Qdrant**: Host, Port, Collection Name
-   **Neo4j**: URI, Username, Password

## 示例代码

```python
from hello_agents.memory.types.semantic import SemanticMemory
from hello_agents.core.config import Config

# 初始化
config = Config()
semantic_mem = SemanticMemory(config.memory)

# 添加记忆
memory_item = MemoryItem(
    content="HelloAgents 是一个基于 LLM 的多智能体框架，支持混合记忆系统。",
    memory_type="semantic"
)
semantic_mem.add(memory_item)

# 检索
results = semantic_mem.retrieve("HelloAgents 有什么特点？")
for res in results:
    print(f"Content: {res.content}, Score: {res.metadata['combined_score']}")
```
