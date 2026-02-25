# 架构设计文档

## 概述

本项目采用**领域驱动设计（DDD）**和**MVC架构**，确保代码的低耦合、高内聚和可扩展性。这种设计使得后续添加新功能时不会影响现有代码。

## 分层架构

### 1. 领域层 (Domain Layer)

**位置**: `backend/domain/`

**职责**: 核心业务逻辑和领域模型

**组成**:
- **entities/**: 领域实体
  - `Conversation`: 对话实体，维护对话状态
  - `FlightLog`: 飞行日志实体
  - `Message`: 消息实体
- **value_objects/**: 值对象
  - `Query`: 用户查询值对象
  - `QueryResult`: 查询结果值对象
- **repositories/**: 仓储接口（抽象）
  - `IFlightLogRepository`: 飞行日志仓储接口
  - `IConversationRepository`: 对话仓储接口

**特点**:
- 不依赖任何外部框架
- 纯业务逻辑
- 通过接口定义，不关心具体实现

### 2. 应用层 (Application Layer)

**位置**: `backend/application/`

**职责**: 用例编排和应用服务

**组成**:
- **use_cases/**: 用例
  - `ChatUseCase`: 聊天用例，处理用户查询的核心逻辑
- **services/**: 应用服务
  - `ChatService`: 聊天服务，封装聊天相关业务
  - `TelemetryService`: 遥测数据服务

**特点**:
- 协调领域对象完成业务用例
- 不包含业务逻辑，只负责编排
- 依赖领域层接口

### 3. 基础设施层 (Infrastructure Layer)

**位置**: `backend/infrastructure/`

**职责**: 外部依赖和技术实现

**组成**:
- **llm/**: LLM客户端
  - `ILLMClient`: LLM客户端接口
  - `OpenAIClient`: OpenAI实现
  - `AnthropicClient`: Anthropic实现
  - `LLMFactory`: LLM工厂
- **parsers/**: 文件解析器
  - `MAVLinkParser`: MAVLink文件解析器
- **storage/**: 存储实现
  - `MemoryFlightLogRepository`: 内存飞行日志仓储实现
  - `MemoryConversationRepository`: 内存对话仓储实现

**特点**:
- 实现领域层定义的接口
- 可替换（如更换LLM提供商、存储后端）
- 隔离外部依赖

### 4. 表现层 (Presentation Layer)

**位置**: `backend/presentation/`

**职责**: 用户界面和API接口

**组成**:
- **api/**: API路由
  - `main.py`: FastAPI应用入口
- **controllers/**: 控制器
  - `ChatController`: 聊天控制器
- **dtos/**: 数据传输对象
  - `ChatRequest`: 聊天请求DTO
  - `ChatResponse`: 聊天响应DTO
  - `FileUploadResponse`: 文件上传响应DTO

**特点**:
- 处理HTTP请求/响应
- 数据验证和转换
- 依赖应用层服务

## 依赖关系

```
Presentation Layer
    ↓ (依赖)
Application Layer
    ↓ (依赖)
Domain Layer
    ↑ (实现)
Infrastructure Layer
```

**关键原则**:
- 依赖方向：外层依赖内层
- 领域层不依赖任何其他层
- 基础设施层实现领域层接口

## 设计模式

### 1. Repository Pattern（仓储模式）

**目的**: 抽象数据访问逻辑

**实现**:
- 领域层定义接口（`IFlightLogRepository`, `IConversationRepository`）
- 基础设施层实现接口（`MemoryFlightLogRepository`, `MemoryConversationRepository`）

**好处**:
- 业务逻辑不依赖具体存储实现
- 易于切换存储后端（内存 → 数据库 → 文件系统）

### 2. Dependency Injection（依赖注入）

**目的**: 解耦组件依赖

**实现**:
- `DIContainer`类管理所有依赖
- 通过构造函数注入依赖

**好处**:
- 易于测试（可注入Mock对象）
- 易于替换实现

### 3. Factory Pattern（工厂模式）

**目的**: 创建对象

**实现**:
- `LLMFactory`根据配置创建LLM客户端

**好处**:
- 统一创建逻辑
- 易于扩展新的LLM提供商

### 4. Use Case Pattern（用例模式）

**目的**: 封装业务用例

**实现**:
- `ChatUseCase`封装聊天业务逻辑

**好处**:
- 业务逻辑清晰
- 易于测试和维护

## 低耦合设计

### 1. 接口抽象

所有外部依赖都通过接口定义：
- `ILLMClient`: LLM客户端接口
- `IFlightLogRepository`: 飞行日志仓储接口
- `IConversationRepository`: 对话仓储接口

### 2. 依赖倒置

高层模块不依赖低层模块，都依赖抽象：
- 应用层依赖仓储接口，不依赖具体实现
- 用例依赖LLM接口，不依赖具体LLM提供商

### 3. 单一职责

每个类只负责一个职责：
- `ChatUseCase`: 处理聊天用例
- `TelemetryService`: 处理遥测数据
- `MAVLinkParser`: 解析MAVLink文件

## 扩展性

### 添加新LLM提供商

1. 实现`ILLMClient`接口
2. 在`LLMFactory`中注册
3. 无需修改其他代码

### 添加新存储后端

1. 实现`IFlightLogRepository`和`IConversationRepository`接口
2. 在`DIContainer`中替换实现
3. 无需修改业务逻辑

### 添加新功能模块

1. 在`application/use_cases/`下创建新用例
2. 在`application/services/`下创建新服务（如需要）
3. 在`presentation/`下添加新的API和控制器
4. 各模块互不干扰

## 测试策略

### 单元测试

- **领域层**: 测试业务逻辑（不依赖外部）
- **应用层**: Mock仓储和LLM客户端
- **基础设施层**: 测试具体实现

### 集成测试

- 测试各层之间的协作
- 使用真实或测试数据库

### 端到端测试

- 测试完整API流程
- 使用测试LLM客户端

## 总结

本架构设计确保了：

1. **低耦合**: 通过接口抽象和依赖注入
2. **高内聚**: 每层职责清晰
3. **可扩展**: 易于添加新功能
4. **可测试**: 依赖可Mock
5. **可维护**: 代码结构清晰

这种设计使得后续添加新功能时，只需在相应层添加代码，不会影响现有功能。

