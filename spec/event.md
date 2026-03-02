# Event Schema v0.1

> 最小对象定义 - Event / Derivation / Commit

---

## 概述

Event是LayCache的**原子单位**，代表一次不可变的数据捕获。

---

## Event 对象

### 字段定义

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | UUID v4, 去掉连字符 |
| `timestamp` | ISO8601 | ✅ | UTC时间戳 |
| `type` | enum | ✅ | `capture` \| `derivation` \| `commit` |
| `content` | string | ✅ | 用户输入内容（加密前） |
| `hash` | string | ✅ | SHA-256 of content |
| `prev_hash` | string? | ❌ | 前一个Event的hash（链式） |
| `device_id` | string | ✅ | 设备唯一标识 |
| `payload_encrypted` | boolean | ❌ | 是否加密（默认false） |

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://laycache.dev/schemas/event-v0.json",
  "title": "LayCache Event v0",
  "type": "object",
  "required": ["id", "timestamp", "type", "content", "hash", "device_id"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$",
      "description": "UUID v4, 去掉连字符"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC时间戳"
    },
    "type": {
      "type": "string",
      "enum": ["capture", "derivation", "commit"],
      "description": "Event类型"
    },
    "content": {
      "type": "string",
      "description": "用户输入内容"
    },
    "hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA-256 hash of content"
    },
    "prev_hash": {
      "type": ["string", "null"],
      "pattern": "^[a-f0-9]{64}$",
      "description": "前一个Event的hash（链式）"
    },
    "device_id": {
      "type": "string",
      "description": "设备唯一标识"
    },
    "payload_encrypted": {
      "type": "boolean",
      "default": false,
      "description": "是否加密"
    }
  }
}
```

### 示例

```json
{
  "id": "a1b2c3d4e5f6789012345678abcdef90",
  "timestamp": "2026-03-02T14:30:00Z",
  "type": "capture",
  "content": "明天下午3点开会",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "prev_hash": null,
  "device_id": "dev_abc123def456",
  "payload_encrypted": false
}
```

---

## Derivation 对象

派生对象，代表从Event派生的AI生成内容。

### 字段定义

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | UUID v4 |
| `event_id` | string | ✅ | 关联的Event ID |
| `type` | enum | ✅ | `summary` \| `classify` \| `extract` |
| `content` | string | ✅ | 派生内容 |
| `model` | string | ✅ | 使用的模型（如`gpt-4`） |
| `model_version` | string | ✅ | 模型版本 |
| `confidence` | float | ❌ | 置信度（0.0-1.0） |
| `input_hashes` | array | ✅ | 输入Event的hash数组 |

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://laycache.dev/schemas/derivation-v0.json",
  "title": "LayCache Derivation v0",
  "type": "object",
  "required": ["id", "event_id", "type", "content", "model", "model_version", "input_hashes"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$"
    },
    "event_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$",
      "description": "关联的Event ID"
    },
    "type": {
      "type": "string",
      "enum": ["summary", "classify", "extract"],
      "description": "派生类型"
    },
    "content": {
      "type": "string",
      "description": "派生内容"
    },
    "model": {
      "type": "string",
      "description": "使用的模型"
    },
    "model_version": {
      "type": "string",
      "description": "模型版本"
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "置信度"
    },
    "input_hashes": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^[a-f0-9]{64}$"
      },
      "description": "输入Event的hash数组"
    }
  }
}
```

---

## Commit 对象

提交对象，代表一个可回滚的快照点。

### 字段定义

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | UUID v4 |
| `timestamp` | ISO8601 | ✅ | UTC时间戳 |
| `event_ids` | array | ✅ | 包含的Event ID数组 |
| `message` | string | ❌ | 提交消息 |
| `parent_commit_id` | string? | ❌ | 父Commit ID（链式） |

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://laycache.dev/schemas/commit-v0.json",
  "title": "LayCache Commit v0",
  "type": "object",
  "required": ["id", "timestamp", "event_ids"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "event_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^[a-f0-9]{32}$"
      },
      "description": "包含的Event ID数组"
    },
    "message": {
      "type": "string",
      "description": "提交消息"
    },
    "parent_commit_id": {
      "type": ["string", "null"],
      "pattern": "^[a-f0-9]{32}$",
      "description": "父Commit ID"
    }
  }
}
```

---

## Hash 计算规则

### Event Hash

```
hash_input = "{id}|{type}|{content}|{timestamp}|{device_id}"
hash = SHA256(hash_input)
```

**示例：**

```python
import hashlib

def compute_event_hash(event):
    hash_input = f"{event.id}|{event.type}|{event.content}|{event.timestamp}|{event.device_id}"
    return hashlib.sha256(hash_input.encode()).hexdigest()
```

### Derivation Input Hashes

```
input_hashes = [SHA256(event1.content), SHA256(event2.content), ...]
```

**或者：**

```
combined = "".join(sorted(event_hashes))
input_hash = SHA256(combined)
```

**决策：** 使用简单方案 - 存储每个输入Event的hash数组。

---

## 链式验证

### Event Chain

```python
def verify_event_chain(events):
    if not events:
        return True, None
    
    # 第一个Event必须没有prev_hash
    if events[0].prev_hash is not None:
        return False, events[0].id
    
    # 后续Event的prev_hash必须等于前一个的hash
    for i in range(1, len(events)):
        if events[i].prev_hash != events[i-1].hash:
            return False, events[i].id
    
    return True, None
```

### Commit Chain

```python
def verify_commit_chain(commits):
    if not commits:
        return True, None
    
    # 第一个Commit必须没有parent_commit_id
    if commits[0].parent_commit_id is not None:
        return False, commits[0].id
    
    # 后续Commit的parent_commit_id必须等于前一个的id
    for i in range(1, len(commits)):
        if commits[i].parent_commit_id != commits[i-1].id:
            return False, commits[i].id
    
    return True, None
```

---

## 迁移路径

### V0 → V0.5（加密）

1. 添加 `payload_encrypted` 字段
2. 实现AES-256-GCM加密
3. `content`字段存储密文（base64编码）

### V0.5 → V1（完整）

1. 添加 `metadata` 字段（可选）
2. 添加 `tags` 字段（数组）
3. 实现 `derivation` 对象

---

## 待决策问题

### 1. ID生成策略

**选项：**
- A. 纯随机UUID v4
- B. 基于内容hash（去重）
- C. 时间戳+随机数

**决策：** ✅ **A - 纯随机UUID v4**

**理由：**
- 简单可靠
- 不依赖内容
- 支持修改（修改后是新Event）

### 2. prev_hash语义

**选项：**
- A. 全局链（所有Event一条链）
- B. 分页链（每个Page一条链）
- C. 无链（独立Event）

**决策：** ✅ **A - 全局链**

**理由：**
- 简单实现
- 完整历史
- 支持全局审计

### 3. Hash计算时机

**选项：**
- A. 创建时计算，存储
- B. 读取时计算，验证
- C. 两者都做

**决策：** ✅ **C - 创建时计算+存储，读取时验证**

**理由：**
- 创建时存储：快速读取
- 读取时验证：安全可靠

---

## 实现状态

| 项目 | 状态 | 位置 |
|------|------|------|
| Event Schema | ✅ 完成 | spec/event.md |
| Derivation Schema | ✅ 完成 | spec/event.md |
| Commit Schema | ✅ 完成 | spec/event.md |
| JSON Schema文件 | ⏳ 待创建 | schemas/*.json |
| 示例数据 | ⏳ 待创建 | examples/*.json |
| 链式验证代码 | ✅ 已有 | LayCacheDB.swift |

---

*此文档解决 Issue #1*
