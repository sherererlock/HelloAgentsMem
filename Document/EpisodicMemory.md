# 情景记忆 (Episodic Memory)

情景记忆用于存储具体的交互事件，包含丰富的上下文信息，按时间序列组织，并支持模式识别和回溯。

## 1. 记忆抽象

基础记忆项包含以下通用字段：

- **id**: 记忆项的唯一标识符
- **user_id**: 记忆项所属用户的唯一标识符
- **content**: 记忆项的具体内容
- **memory_type**: 记忆项的类型，例如 "episodic"
- **timestamp**: 记忆项的创建时间
- **importance**: 记忆项的重要性评分，范围从 0 到 1
- **metadata**: 额外的元数据，用于存储与记忆项相关的信息

## 2. 情景抽象 (Episode)

情景记忆在基础记忆项之上增加了特定字段，由 `Episode` 类表示：

- **episode_id**: 情景项的唯一标识符 (对应 memory_id)
- **user_id**: 情景项所属用户的唯一标识符
- **session_id**: 情景项所属会话的唯一标识符
- **timestamp**: 情景项的创建时间
- **content**: 情景项的具体内容
- **context**: 情景项的上下文 (Dict)，描述情景发生的环境和条件
- **outcome**: 情景项的结果 (Optional)，描述情景发生后对用户或环境的影响
- **importance**: 情景项的重要性评分，范围从 0 到 1

## 3. 情景记忆实现 (EpisodicMemory)

`EpisodicMemory` 类继承自 `BaseMemory`，提供以下核心能力：
- **多级存储**: 内存缓存 + SQLite (权威存储) + Qdrant (向量索引)
- **混合检索**: 结合结构化过滤和向量语义检索
- **智能评分**: 综合考虑相似度、近因效应 (Recency) 和重要性 (Importance)
- **遗忘机制**: 支持基于时间、重要性和容量的硬删除策略

### 3.1 添加记忆项 (Add)

添加过程涉及三级存储：

1.  **内存缓存**: 创建 `Episode` 对象并存入 `self.episodes` 列表，同时更新 `self.sessions` 索引。
2.  **权威存储 (SQLite)**:
    *   将完整信息存储在 SQLite 数据库中。
    *   `properties` 字段存储 `session_id`, `context`, `outcome`, `participants`, `tags` 等扩展信息。
3.  **向量索引 (Qdrant)**:
    *   对 `content` 进行向量化 (Embedding)。
    *   存储向量及 Payload (Metadata): `memory_id`, `user_id`, `memory_type`, `importance`, `session_id`, `content`。

### 3.2 检索记忆项 (Retrieve)

检索过程采用 "结构化过滤 -> 向量检索 -> 综合评分" 的流程：

1.  **结构化过滤 (SQLite)**:
    *   根据 `user_id`, `session_id`, `time_range`, `importance_threshold` 等条件在 SQLite 中筛选候选 `memory_id` 集合。

2.  **向量检索 (Qdrant)**:
    *   将 `query` 向量化。
    *   在 Qdrant 中搜索相似向量 (可带 `user_id` 过滤)。
    *   获取 Top K 结果及其向量相似度分数 (`vec_score`)。

3.  **综合评分**:
    *   对每个检索到的结果，结合 SQLite 中的完整信息进行评分。
    *   **近因分数 (Recency Score)**: `recency_score = 1.0 / (1.0 + age_days)`
    *   **基础相关性 (Base Relevance)**: `base_relevance = vec_score * 0.8 + recency_score * 0.2`
    *   **重要性权重 (Importance Weight)**: `importance_weight = 0.8 + (imp * 0.4)`
    *   **最终得分 (Combined Score)**: `combined = base_relevance * importance_weight`

4.  **回退机制 (Fallback)**:
    *   如果向量检索无结果，回退到**内存关键词匹配**。
    *   在 `self.episodes` 中进行关键词搜索。
    *   匹配项给予基础分 `0.5`，再结合近因和重要性计算最终得分。

### 3.3 更新记忆 (Update)

支持更新 `content`, `importance` 和 `metadata`：

1.  **内存更新**: 更新 `self.episodes` 中的对应对象。
2.  **SQLite 更新**: 更新数据库中的对应记录。
3.  **Qdrant 更新**:
    *   如果 `content` 发生变化，重新计算 Embedding。
    *   使用新的向量和 Payload 覆盖原有记录。

### 3.4 删除记忆项 (Remove)

删除操作会同步清理所有存储层：

1.  **内存**: 从 `self.episodes` 和 `self.sessions` 中移除。
2.  **SQLite**: 删除对应记录。
3.  **Qdrant**: 删除对应向量。

### 3.5 清空记忆 (Clear)

清空所有情景类型的记忆：
*   清空内存列表和字典。
*   从 SQLite 中删除所有 `memory_type="episodic"` 的记录。
*   从 Qdrant 中删除对应的向量。

## 4. 遗忘机制 (Forget)

`forget` 方法实现了**硬删除**策略，支持三种模式：

1.  **基于重要性 (importance_based)**: 删除 `importance` 低于 `threshold` 的记忆。
2.  **基于时间 (time_based)**: 删除 `timestamp` 早于 `max_age_days` 的记忆。
3.  **基于容量 (capacity_based)**: 当记忆数量超过 `max_capacity` 时，保留重要性最高的记忆，删除多余的。

遗忘操作会调用 `remove` 方法，彻底从所有存储介质中删除数据。

## 5. 其他功能

- **获取所有记忆 (get_all)**: 返回所有情景记忆的列表。
- **获取会话记忆 (get_session_episodes)**: 获取指定 `session_id` 的所有情景。
- **模式识别 (find_patterns)**: 基于简单的关键词和上下文统计，发现用户行为模式。
- **获取统计 (get_stats)**: 返回记忆数量、会话数、平均重要性、时间跨度以及底层存储 (SQLite/Qdrant) 的统计信息。
