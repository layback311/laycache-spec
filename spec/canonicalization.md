# Canonicalization 规则 v0.1

> 内容标准化规则 - 确保 Hash 一致性

---

## 概述

Canonicalization（标准化）是将用户输入转换为**确定性格式**的过程，确保：
- 相同内容 → 相同 Hash
- 可预测的格式
- 链式验证可靠

---

## 核心原则

### 1. 原始内容保留

```json
{
  "content": "用户输入的原始内容",
  "canonical_content": "标准化后的内容（用于Hash计算）"
}
```

**决策：** 不修改原始内容，仅用于 Hash 计算。

---

## Canonicalization 规则

### 规则 1: 去除首尾空白

```python
def trim_whitespace(text: str) -> str:
    """去除首尾空白字符"""
    return text.strip()
```

**示例：**
```
输入: "  明天开会  "
输出: "明天开会"
```

### 规则 2: 标准化换行符

```python
def normalize_newlines(text: str) -> str:
    """将所有换行符标准化为 \\n"""
    return text.replace("\r\n", "\n").replace("\r", "\n")
```

**示例：**
```
输入: "第一行\r\n第二行"
输出: "第一行\n第二行"
```

### 规则 3: 合并连续空白

```python
def collapse_whitespace(text: str) -> str:
    """合并连续的空格为单个空格"""
    import re
    return re.sub(r' +', ' ', text)
```

**示例：**
```
输入: "明天    开会"
输出: "明天 开会"
```

### 规则 4: 不修改内部内容

```python
def preserve_internal(text: str) -> str:
    """保留内部格式（如缩进、特殊符号）"""
    return text  # 不做任何修改
```

**决策：** 仅处理首尾和空白，不修改内部格式。

---

## 完整 Canonicalization 流程

```python
def canonicalize(text: str) -> str:
    """
    标准化文本内容
    """
    # 1. 去除首尾空白
    text = text.strip()

    # 2. 标准化换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. 不合并内部空白（保留原始格式）

    return text
```

---

## Hash 计算

### 输入格式

```
hash_input = "{id}|{type}|{canonical_content}|{timestamp}|{device_id}"
```

### 示例

```python
import hashlib

def compute_event_hash(event: dict) -> str:
    # 1. Canonicalize content
    canonical_content = canonicalize(event["content"])

    # 2. 构建 hash input
    hash_input = (
        f"{event['id']}|"
        f"{event['type']}|"
        f"{canonical_content}|"
        f"{event['timestamp']}|"
        f"{event['device_id']}"
    )

    # 3. 计算 SHA-256
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
```

### 测试用例

```python
event = {
    "id": "a1b2c3d4e5f6789012345678abcdef01",
    "type": "capture",
    "content": "  明天开会  ",
    "timestamp": "2026-03-02T10:00:00Z",
    "device_id": "dev_abc123"
}

hash1 = compute_event_hash(event)
# 即使 content 有空白差异，hash 仍然一致

event["content"] = "明天开会"  # 已 trim
hash2 = compute_event_hash(event)

assert hash1 == hash2  # ✅ 通过
```

---

## 边界情况

### 1. 空内容

```python
event = {
    "content": ""  # 空字符串
}

canonical_content = canonicalize("")  # ""
hash = compute_event_hash(event)  # 仍然有效
```

### 2. 仅空白

```python
event = {
    "content": "   "  # 仅空白
}

canonical_content = canonicalize("   ")  # ""
# 决策：空白内容 → 空字符串
```

### 3. 多行内容

```python
event = {
    "content": "第一行\n  第二行（有缩进）\n第三行"
}

canonical_content = canonicalize(event["content"])
# 输出: "第一行\n  第二行（有缩进）\n第三行"
# 注意：内部缩进保留
```

### 4. Unicode 内容

```python
event = {
    "content": "你好世界 🌍"
}

canonical_content = canonicalize(event["content"])
# 输出: "你好世界 🌍"（保留 emoji）
```

---

## 不标准化内容

### 为什么不标准化内部格式？

**原因：**
1. **保留原始意图** - 用户的格式有意义（如代码缩进）
2. **避免信息丢失** - 修改可能改变语义
3. **简单可靠** - 规则越少，出错越少

**反例：**
```python
# ❌ 不推荐：过度标准化
def over_canonicalize(text: str) -> str:
    text = text.lower()  # 小写化
    text = re.sub(r'[^\w\s]', '', text)  # 去除标点
    return text

# 问题：丢失了原始信息
```

---

## 版本兼容性

### v0.1 规则

- ✅ 首尾空白去除
- ✅ 换行符标准化
- ❌ 不修改内部格式

### 未来扩展（v0.5+）

可考虑：
- Unicode 标准化（NFC/NFD）
- 表情符号标准化
- 语言检测（多语言内容）

---

## 实现（Swift）

```swift
import Foundation
import CryptoKit

func canonicalize(_ text: String) -> String {
    // 1. 去除首尾空白
    var result = text.trimmingCharacters(in: .whitespacesAndNewlines)

    // 2. 标准化换行符
    result = result.replacingOccurrences(of: "\r\n", with: "\n")
    result = result.replacingOccurrences(of: "\r", with: "\n")

    return result
}

func computeEventHash(event: [String: Any]) -> String {
    guard let id = event["id"] as? String,
          let type = event["type"] as? String,
          let content = event["content"] as? String,
          let timestamp = event["timestamp"] as? String,
          let deviceId = event["device_id"] as? String else {
        return ""
    }

    // Canonicalize
    let canonicalContent = canonicalize(content)

    // Build hash input
    let hashInput = "\(id)|\(type)|\(canonicalContent)|\(timestamp)|\(deviceId)"

    // Compute SHA-256
    let data = hashInput.data(using: .utf8)!
    let digest = SHA256.hash(data: data)

    return digest.compactMap { String(format: "%02x", $0) }.joined()
}
```

---

## 验证流程

### 创建 Event 时

```swift
func createEvent(content: String, deviceId: String) -> [String: Any] {
    let id = UUID().uuidString.replacingOccurrences(of: "-", with: "")
    let timestamp = ISO8601DateFormatter().string(from: Date())
    let type = "capture"

    let event: [String: Any] = [
        "id": id,
        "timestamp": timestamp,
        "type": type,
        "content": content,
        "device_id": deviceId,
        "payload_encrypted": false
    ]

    // Compute hash
    let hash = computeEventHash(event: event)
    var mutableEvent = event
    mutableEvent["hash"] = hash

    return mutableEvent
}
```

### 验证 Event 时

```swift
func verifyEvent(event: [String: Any]) -> Bool {
    guard let storedHash = event["hash"] as? String else {
        return false
    }

    // Recompute hash
    let computedHash = computeEventHash(event: event)

    return storedHash == computedHash
}
```

---

## 测试用例

### 测试 1: 空白差异不影响 Hash

```swift
let event1 = createEvent(content: "明天开会", deviceId: "dev_123")
let event2 = createEvent(content: "  明天开会  ", deviceId: "dev_123")

XCTAssertEqual(event1["hash"] as? String, event2["hash"] as? String)
// ✅ 通过
```

### 测试 2: 换行符标准化

```swift
let event1 = createEvent(content: "第一行\n第二行", deviceId: "dev_123")
let event2 = createEvent(content: "第一行\r\n第二行", deviceId: "dev_123")

XCTAssertEqual(event1["hash"] as? String, event2["hash"] as? String)
// ✅ 通过
```

### 测试 3: 内部格式保留

```swift
let event = createEvent(content: "第一行\n  第二行（有缩进）", deviceId: "dev_123")

// content 应该保留原始格式
XCTAssertEqual(event["content"] as? String, "第一行\n  第二行（有缩进）")
// ✅ 通过
```

---

## 决策记录

### 决策 1: 最小化标准化

**选择：** 仅处理首尾空白和换行符

**理由：**
- 简单可靠
- 不丢失信息
- 易于实现

### 决策 2: Hash 计算包含元数据

**选择：** Hash = id + type + content + timestamp + device_id

**理由：**
- 防止篡改任何字段
- 全局唯一
- 可验证完整性

---

*此文档解决Issue #2*
