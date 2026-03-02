# Week 1: Why I'm Building a Local-First Memory Ledger

## 我遇到的问题

作为一个 AI Agent 的"主人"，我发现了一个痛点：

**碎片化**。

我的想法、任务、备忘录、聊天记录...分散在各个 app 里。Evernote、Apple Notes、iMessage、飞书、Telegram...

每当我需要回顾某件事时，要翻好几个 app。

**丢失上下文**。

更严重的是，AI 生成的总结经常"失忆"。今天问它上周讨论的内容，它不记得了。或者给了一个错误的理解。

**不可追溯**。

当 AI 给出建议时，我无法追溯：
- 它参考了哪些信息？
- 推理过程是什么？
- 如果错了，如何回滚？

这些问题让我意识到：**我需要一个"记忆账本"**。

---

## 我在做什么：LayCache

**LayCache = Layer + Cache**

一个分层的、可追溯的记忆系统。

### 核心设计

| 功能 | 说明 |
|------|------|
| 📝 Event Sourcing | 每条记录都是不可变的事件 |
| 🔄 Commit-based Rollback | 可以回滚到任意历史版本 |
| 🔍 External Audit | 追踪 AI 如何处理我的数据 |
| 📦 Portable Export | 可导出完整的记忆包 |

### 技术栈

- **iOS/Swift** - 参考实现
- **SQLite** - 本地存储
- **AES-256-GCM** - 加密
- **Face ID** - 身份验证

---

## 我不做什么

明确边界很重要：

- ❌ **不默认云同步** - 数据优先存储在本地
- ❌ **不出卖用户数据** - 这是个人工具，不是商业产品
- ❌ **不依赖网络** - 核心功能离线可用
- ❌ **不锁定平台** - 数据可导出，协议开放

---

## 路线图

| 版本 | 目标 | 时间 |
|------|------|------|
| **v0.1** | 事件存储 + 基础 UI | ✅ 已完成 |
| **v0.5** | 加密 + Face ID | ⏳ 进行中 |
| **v1.0** | 完整 inbox + classification | 📋 Q2 |
| **v2.0** | Derivation layer (AI 总结) | 📋 Q3 |
| **v3.0** | Audit trail + 外发推理追踪 | 📋 Q4 |
| **v4.0** | 协议冻结 + 文档 | 📋 2026 |
| **v5.0+** | SDK + 一致性测试 | 🔮 未来 |

---

## 证据链

本周完成的工作：

| 任务 | 链接 |
|------|------|
| 项目结构定义 | GitHub: laycache-spec |
| Event Schema 设计 | Issue #1 |
| Export Bundle 设计 | Issue #4 |
| 示例数据集 | Issue #7 |

---

## 公开但不透露

本周有一些内容因为隐私/安全暂不公开：

- 🔒 真实的用户数据示例
- 🔒 加密实现细节
- 🔒 API 密钥
- 🔒 云端推理请求原文

---

## 下周计划

- [ ] 完成 v0.5 加密功能
- [ ] 创建 laycache-spec GitHub repo
- [ ] 写 JSON Schema v0
- [ ] 准备第一篇 Substack 文章

---

# EN: Why I'm Building a Local-First Memory Ledger

## The Problem

As someone who relies on AI agents, I found a pain point: **fragmentation**.

My thoughts, tasks, notes, and chat history are scattered across Evernote, Apple Notes, iMessage, Feishu, Telegram...

Every time I need to recall something, I have to search through multiple apps.

**Lost Context**: AI-generated summaries often "forget". When I ask about last week's discussion, it doesn't remember. Or it gives a wrong understanding.

**Not Traceable**: When AI gives advice, I can't trace:
- What information did it reference?
- What was the reasoning process?
- If it's wrong, how do I rollback?

## What I'm Building: LayCache

**LayCache = Layer + Cache**

A layered, traceable memory system.

### Core Features

| Feature | Description |
|---------|-------------|
| 📝 Event Sourcing | Every record is an immutable event |
| 🔄 Commit-based Rollback | Roll back to any historical version |
| 🔍 External Audit | Track how AI processes your data |
| 📦 Portable Export | Export complete memory bundle |

### Tech Stack

- **iOS/Swift** - Reference implementation
- **SQLite** - Local storage
- **AES-256-GCM** - Encryption
- **Face ID** - Authentication

---

## What I'm NOT Doing

- ❌ No cloud sync by default - Data stays local first
- ❌ No selling user data - This is a personal tool, not a commercial product
- ❌ No network dependency - Core features work offline
- ❌ No platform lock-in - Data is exportable, protocol is open

---

## Roadmap

See [ROADMAP.md](link) for full details.

---

## Next Week

- [ ] Complete v0.5 encryption
- [ ] Create laycache-spec GitHub repo
- [ ] Write JSON Schema v0
- [ ] Prepare first Substack post

---

*Published: 2026-03-02*
*Tags: laycache, local-first, memory, privacy*
