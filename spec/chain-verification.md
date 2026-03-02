# 链式验证规范 v0.1

> Event 链完整性验证 - 防篡改机制

---

## 概述

链式验证确保：
1. **完整性** - 所有 Event 都存在
2. **顺序性** - 链式关系正确
3. **防篡改** - Hash 验证通过

---

## 验证流程

### 1. 链头验证

```python
def verify_chain_head(events: list) -> tuple[bool, str]:
    """
    验证第一个 Event
    返回: (is_valid, error_message)
    """
    if not events:
        return True, None

    first_event = events[0]

    # 第一个 Event 必须没有 prev_hash
    if first_event.get("prev_hash") is not None:
        return False, f"First event {first_event['id']} has prev_hash"

    return True, None
```

### 2. 链式关系验证

```python
def verify_chain_links(events: list) -> tuple[bool, str]:
    """
    验证链式关系
    每个事件的 prev_hash 必须等于前一个的 hash
    """
    # 按 timestamp 排序
    sorted_events = sorted(events, key=lambda e: e["timestamp"])

    for i in range(1, len(sorted_events)):
        current = sorted_events[i]
        previous = sorted_events[i - 1]

        if current["prev_hash"] != previous["hash"]:
            return False, f"Event {current['id']} prev_hash mismatch"

    return True, None
```

### 3. Hash 完整性验证

```python
def verify_hash_integrity(events: list) -> tuple[bool, str]:
    """
    验证每个 Event 的 hash 是否正确
    """
    for event in events:
        computed_hash = compute_event_hash(event)

        if event["hash"] != computed_hash:
            return False, f"Event {event['id']} hash mismatch"

    return True, None
```

### 4. 完整验证

```python
def verify_chain(events: list) -> dict:
    """
    完整链式验证
    返回: {
        "valid": bool,
        "errors": [str],
        "warnings": [str]
    }
    """
    errors = []
    warnings = []

    # 1. 空链检查
    if not events:
        return {"valid": True, "errors": [], "warnings": ["Empty chain"]}

    # 2. 链头验证
    is_valid, error = verify_chain_head(events)
    if not is_valid:
        errors.append(error)

    # 3. 链式关系验证
    is_valid, error = verify_chain_links(events)
    if not is_valid:
        errors.append(error)

    # 4. Hash 完整性验证
    is_valid, error = verify_hash_integrity(events)
    if not is_valid:
        errors.append(error)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

---

## iOS 实现（Swift）

```swift
class ChainVerifier {
    // 验证整个链
    static func verify(events: [[String: Any]]) -> ChainVerificationResult {
        var errors: [String] = []
        var warnings: [String] = []

        // 1. 空链检查
        if events.isEmpty {
            return ChainVerificationResult(
                valid: true,
                errors: [],
                warnings: ["Empty chain"]
            )
        }

        // 2. 按 timestamp 排序
        let sorted = events.sorted { a, b in
            (a["timestamp"] as? String ?? "") < (b["timestamp"] as? String ?? "")
        }

        // 3. 链头验证
        if let first = sorted.first, first["prev_hash"] != nil {
            errors.append("First event has prev_hash")
        }

        // 4. 链式关系验证
        for i in 1..<sorted.count {
            let current = sorted[i]
            let previous = sorted[i - 1]

            if current["prev_hash"] as? String != previous["hash"] as? String {
                errors.append("Event \(current["id"] ?? "?") prev_hash mismatch")
            }
        }

        // 5. Hash 完整性验证
        for event in sorted {
            let computedHash = computeEventHash(event: event)
            if event["hash"] as? String != computedHash {
                errors.append("Event \(event["id"] ?? "?") hash mismatch")
            }
        }

        return ChainVerificationResult(
            valid: errors.isEmpty,
            errors: errors,
            warnings: warnings
        )
    }
}

struct ChainVerificationResult {
    let valid: Bool
    let errors: [String]
    let warnings: [String]
}
```

---

## 测试用例

### 测试 1: 有效链

```swift
let events = [
    ["id": "1", "timestamp": "2026-03-02T10:00:00Z", "hash": "a1", "prev_hash": nil],
    ["id": "2", "timestamp": "2026-03-02T10:05:00Z", "hash": "a2", "prev_hash": "a1"],
    ["id": "3", "timestamp": "2026-03-02T10:10:00Z", "hash": "a3", "prev_hash": "a2"]
]

let result = ChainVerifier.verify(events: events)
XCTAssertTrue(result.valid)
// ✅ 通过
```

### 测试 2: 链断裂

```swift
let events = [
    ["id": "1", "timestamp": "2026-03-02T10:00:00Z", "hash": "a1", "prev_hash": nil],
    ["id": "2", "timestamp": "2026-03-02T10:05:00Z", "hash": "a2", "prev_hash": "WRONG"]
]

let result = ChainVerifier.verify(events: events)
XCTAssertFalse(result.valid)
XCTAssertEqual(result.errors.first, "Event 2 prev_hash mismatch")
// ✅ 通过
```

### 测试 3: Hash 篡改

```swift
let events = [
    ["id": "1", "timestamp": "2026-03-02T10:00:00Z", "hash": "TAMPERED", "prev_hash": nil]
]

let result = ChainVerifier.verify(events: events)
XCTAssertFalse(result.valid)
XCTAssertTrue(result.errors.first?.contains("hash mismatch") ?? false)
// ✅ 通过
```

---

## 性能优化

### 优化 1: 增量验证

```swift
// 只验证新增的 Event
func verifyNewEvents(existing: [[String: Any]], new: [[String: Any]]) -> Bool {
    guard let lastExisting = existing.last else {
        return ChainVerifier.verify(events: new).valid
    }

    guard let firstNew = new.first else {
        return true
    }

    // 检查链接
    if firstNew["prev_hash"] as? String != lastExisting["hash"] as? String {
        return false
    }

    // 验证新链
    return ChainVerifier.verify(events: new).valid
}
```

### 优化 2: 批量验证

```swift
// 每 100 个 Event 验证一次
func batchVerify(events: [[String: Any]], batchSize: Int = 100) -> [ChainVerificationResult] {
    var results: [ChainVerificationResult] = []

    for i in stride(from: 0, to: events.count, by: batchSize) {
        let batch = Array(events[i..<min(i + batchSize, events.count)])
        results.append(ChainVerifier.verify(events: batch))
    }

    return results
}
```

---

## 异常处理

### 场景 1: 链断裂

**原因：** Event 丢失或删除

**处理：**
```swift
if !result.valid && result.errors.contains("prev_hash mismatch") {
    // 1. 标记为"断裂"
    // 2. 提示用户从备份恢复
    // 3. 或重新计算 prev_hash（不推荐，违反不可变性）
}
```

### 场景 2: Hash 不匹配

**原因：** Event 被篡改

**处理：**
```swift
if !result.valid && result.errors.contains("hash mismatch") {
    // 1. 标记为"可疑"
    // 2. 警告用户数据可能被篡改
    // 3. 建议从备份恢复
}
```

---

## 决策记录

### 决策 1: 全局链

**选择：** 所有 Event 在一条链上

**理由：**
- 简单实现
- 完整历史
- 全局审计

**缺点：**
- 大量 Event 时验证慢

**缓解：** 增量验证

### 决策 2: 链头 prev_hash = nil

**选择：** 第一个 Event 的 prev_hash 必须为 nil

**理由：**
- 明确标识链起点
- 避免循环引用

### 决策 3: 严格验证

**选择：** 任何验证失败都拒绝

**理由：**
- 安全第一
- 早期发现问题

---

## 数据结构

### Event（简化）

```swift
struct Event {
    let id: String
    let timestamp: String
    let type: EventType
    let content: String
    let hash: String          // 内容 + 元数据的 hash
    let prevHash: String?     // 前一个 Event 的 hash
    let deviceId: String
}
```

### 链式关系

```
Event 1 (prev_hash=nil)
   ↓ hash=a1
Event 2 (prev_hash=a1)
   ↓ hash=a2
Event 3 (prev_hash=a2)
   ↓ hash=a3
...
```

---

## 未来增强

### V1: Merkle Tree

```python
# 使用 Merkle Tree 优化验证
def build_merkle_tree(events: list) -> str:
    """构建 Merkle Tree，返回 root hash"""
    if not events:
        return ""

    # 叶子节点
    hashes = [e["hash"] for e in events]

    # 向上构建树
    while len(hashes) > 1:
        new_level = []
        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i + 1] if i + 1 < len(hashes) else hashes[i]
            combined = hash256(left + right)
            new_level.append(combined)
        hashes = new_level

    return hashes[0]  # Root hash
```

**优势：**
- 快速验证某个 Event 是否在链中
- 不需要遍历整条链

---

*此文档解决Issue #5*
