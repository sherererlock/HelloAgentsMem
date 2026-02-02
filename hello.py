# 配置好同级文件夹下.env中的大模型API
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool, SearchTool
import dotenv

dotenv.load_dotenv()

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建工具注册表
tool_registry = ToolRegistry()

# # 添加记忆工具
# memory_tool = MemoryTool(user_id="user123")
# tool_registry.register_tool(memory_tool)

# # 添加RAG工具
# rag_tool = RAGTool(knowledge_base_path="./knowledge_base")
# tool_registry.register_tool(rag_tool)

# 添加搜索工具
search_tool = SearchTool()
tool_registry.register_tool(search_tool)

# 创建Agent
agent = SimpleAgent(
    name="智能助手",
    llm=llm,
    system_prompt="你是一个AI助手",
    tool_registry=tool_registry,
)

print(agent._get_enhanced_system_prompt())
# 开始对话
response = agent.run("你好！请记住我叫张三，我是一名Python开发者,请告诉我关于大模型的最新动态")
print(response)
