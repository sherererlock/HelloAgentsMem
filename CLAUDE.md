# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HelloAgents is a flexible, extensible multi-agent framework built on OpenAI's native API. It provides a streamlined experience for AI agent development with support for memory systems, tool calling, and RAG (Retrieval-Augmented Generation).

## Architecture

### Core Components

**hello_agents/core/**
- `agent.py`: Base `Agent` abstract class that all agents inherit from
- `llm.py`: `HelloAgentsLLM` - unified LLM client supporting multiple providers (OpenAI, DeepSeek, Qwen, Kimi, Zhipu, Ollama, vLLM, local)
- `config.py`: `Config` class for configuration management
- `message.py`: `Message` class for conversation history
- `exceptions.py`: Custom exception classes

**hello_agents/agents/**
- `simple_agent.py`: `SimpleAgent` - basic conversational agent with optional tool calling
- `react_agent.py`: `ReActAgent` - reasoning and acting paradigm
- `reflection_agent.py`: `ReflectionAgent` - self-reflection agent
- `plan_solve_agent.py`: `PlanAndSolveAgent` - planning-based problem solving

**hello_agents/tools/**
- `base.py`: `Tool` base class and `ToolParameter` for creating custom tools
- `registry.py`: `ToolRegistry` for tool registration and management
- `builtin/`: Built-in tools (Search, Calculator, Memory, RAG)
- `chain.py`: Tool chaining capabilities
- `async_executor.py`: Parallel tool execution

**hello_agents/memory/**
- `manager.py`: `MemoryManager` - unified memory operations interface
- `types/`: Memory types (Working, Episodic, Semantic, Perceptual)
- `storage/`: Storage backends (Qdrant vector store, Neo4j graph store, Document store)
- `rag/`: RAG pipeline for document indexing and retrieval
- `embedding.py`: Unified embedding interface supporting DashScope API and sentence-transformers

### Key Design Patterns

**Tool Calling**: SimpleAgent parses text-based tool calls in format `[TOOL_CALL:tool_name:parameters]`. The agent automatically detects and executes tool calls, with support for parameter inference and multi-iteration tool usage.

**Memory System**: Four-layer architecture with different memory types:
- Working Memory: Short-term, capacity-limited
- Episodic Memory: Personal experiences and events
- Semantic Memory: Facts and concepts
- Perceptual Memory: Sensory information

**RAG Pipeline**: Uses MarkItDown for universal document conversion (PDF, Office docs, images, audio), supports chunking, embedding, and vector search with query expansion (MQE, HyDE) and reranking.
