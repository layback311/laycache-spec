# LayCache V5 - Sync Protocol Specification

> **Version:** 1.0.0 (Alpha)
> **Date:** 2026-03-02
> **Author:** 银月 (器灵)

---

## 1. Overview

V5 验证 append-only 在多设备可行，引入同步协议。

**核心原则：**
- Append-only 是不可逆核心
- Block 不覆盖（只追加）
- Conflict 生成 conflict_event（永远不 LWW）
- 手动同步（iCloud / 本地导入）

---

## 2. Version Vector

### 2.1 Definition

**Version Vector** = 每个设备的最后已知事件时间戳

```json
{
  "dev_abc123": "2026-03-02T21:35:00Z",
  "dev_xyz789": "2026-03-02T21:30:00Z",
  "dev_def456": "2026-03-02T21:40:00Z"
}
```

### 2.2 Usage

```
同步时：
1. 交换双方的 version vector
2. 找出对方缺失的 events
3. 发送缺失的 events（按时间戳）
4. 更新 version vector
```

---

## 3. Device ID in Events

### 3.1 Requirement

**每个 event 必须包含 deviceId**

```json
{
  "eventId": "evt_001",
  "type": "user.preference",
  "content": {...},
  "timestamp": "2026-03-02T21:35:00Z",
  "deviceId": "dev_abc123",  // 必填
  "previousHash": "..."
}
```

### 3.2 Device ID Format

```
dev_<sha256(public_key)>[:8]

Example: dev_a1b2c3d4
```

---

## 4. Merge Strategy

### 4.1 Core Rules

| 规则 | 说明 |
|------|------|
| **Block 不覆盖** | Block 只追加，永不修改 |
| **Conflict Event** | 检测到冲突时生成 conflict_event |
| **永远不 LWW** | 不使用 Last-Write-Wins |

### 4.2 Merge Algorithm

```
1. 加载本地的 events
2. 加载远程的 events
3. 按 (timestamp, deviceId) 排序合并
4. 对于相同 eventId：
   a. 检查哈希是否一致
   b. 一致：正常合并
   c. 不一致：生成 conflict_event
5. 重新计算哈希链
```

### 4.3 Conflict Event

```json
{
  "eventId": "evt_conflict_001",
  "type": "conflict.detected",
  "content": {
    "conflictingEventId": "evt_123",
    "localVersion": {...},
    "remoteVersion": {...},
    "resolution": "manual",  // manual / auto
    "resolvedAt": null
  },
  "timestamp": "2026-03-02T21:45:00Z",
  "deviceId": "dev_abc123"
}
```

---

## 5. Sync Mechanisms

### 5.1 iCloud Sync

```
1. 将 bundle 导出到 iCloud Drive
2. 另一设备检测到变更
3. 下载并合并
4. 上传合并后的 bundle
```

### 5.2 Local Import/Export

```
导出：
1. 生成 bundle（.laycache 文件）
2. 包含 version vector
3. 用户手动传输（AirDrop / USB）

导入：
1. 接收 bundle 文件
2. 验证签名（如果有）
3. 合并 events
4. 生成 conflict events（如果有）
```

### 5.3 Manual Trigger

**V5 不支持自动同步，必须手动触发**

```swift
// 导出
let bundle = db.exportBundle()
try bundle.write(to: iCloudURL)

// 导入
let bundle = try Bundle(url: iCloudURL)
let result = try db.mergeBundle(bundle)
print("Merged \(result.eventsAdded) events")
print("Conflicts: \(result.conflicts.count)")
```

---

## 6. Sync Protocol

### 6.1 Handshake

```json
{
  "protocol": "laycache-sync",
  "version": "1.0.0",
  "deviceId": "dev_abc123",
  "versionVector": {
    "dev_abc123": "2026-03-02T21:35:00Z",
    "dev_xyz789": "2026-03-02T21:30:00Z"
  }
}
```

### 6.2 Sync Request

```json
{
  "type": "sync_request",
  "deviceId": "dev_abc123",
  "since": {
    "dev_xyz789": "2026-03-02T21:30:00Z"
  }
}
```

### 6.3 Sync Response

```json
{
  "type": "sync_response",
  "deviceId": "dev_xyz789",
  "events": [
    {...},
    {...}
  ],
  "newVersionVector": {
    "dev_abc123": "2026-03-02T21:35:00Z",
    "dev_xyz789": "2026-03-02T21:45:00Z"
  }
}
```

---

## 7. Conflict Resolution

### 7.1 Detection

**冲突检测条件：**
- 相同 eventId
- 不同哈希值
- 来自不同设备

### 7.2 Resolution Types

| 类型 | 说明 | 触发条件 |
|------|------|---------|
| **manual** | 手动解决 | 默认 |
| **auto_earliest** | 保留最早的 | 可配置 |
| **auto_latest** | 保留最新的 | 可配置 |

### 7.3 Manual Resolution

```swift
// 获取所有冲突
let conflicts = db.getConflicts()

// 手动选择保留哪个版本
for conflict in conflicts {
    let chosen = conflict.localVersion  // 或 remoteVersion
    db.resolveConflict(conflict.eventId, keepVersion: chosen)
}
```

---

## 8. Two-Device Experiment

### 8.1 Test Plan (30 Days)

| 阶段 | 天数 | 测试内容 |
|------|------|---------|
| **Phase 1** | Day 1-7 | 基础同步，无冲突 |
| **Phase 2** | Day 8-14 | 制造冲突场景 |
| **Phase 3** | Day 15-21 | 离线同步，批量合并 |
| **Phase 4** | Day 22-30 | 压力测试，大容量 |

### 8.2 Conflict Scenarios

| 场景 | 说明 |
|------|------|
| **同时修改** | 两设备同时修改同一event |
| **删除冲突** | 一设备删除，另一设备修改 |
| **顺序冲突** | 哈希链顺序不一致 |
| **时钟漂移** | 设备时间不同步 |

### 8.3 Metrics

| 指标 | 目标 |
|------|------|
| 同步成功率 | > 99% |
| 冲突检测率 | 100% |
| 数据丢失率 | 0% |
| 合并时间 | < 5s (1000 events) |

---

## 9. Conflict Resolution Document

### 9.1 Principles

1. **数据优先** - 宁可保留冲突，不可丢数据
2. **用户主导** - 冲突由用户手动解决（默认）
3. **可追溯** - 所有冲突记录在 conflict_event

### 9.2 Conflict Event Lifecycle

```
1. 检测到冲突 → 创建 conflict_event
2. 用户查看冲突
3. 用户选择保留版本
4. 生成 resolution_event
5. 标记 conflict_event 为 resolved
```

### 9.3 Example

```json
// 1. Conflict detected
{
  "eventId": "evt_conflict_001",
  "type": "conflict.detected",
  "content": {
    "conflictingEventId": "evt_task_001",
    "localVersion": {"status": "completed"},
    "remoteVersion": {"status": "cancelled"},
    "resolution": "manual"
  }
}

// 2. User resolves
{
  "eventId": "evt_resolution_001",
  "type": "conflict.resolved",
  "content": {
    "conflictEventId": "evt_conflict_001",
    "chosenVersion": "local",
    "reason": "用户选择"
  }
}
```

---

## 10. SQL Schema

### 10.1 Version Vectors Table

```sql
CREATE TABLE version_vectors (
    device_id TEXT PRIMARY KEY,
    last_event_timestamp TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 10.2 Conflicts Table

```sql
CREATE TABLE conflicts (
    conflict_id TEXT PRIMARY KEY,
    conflicting_event_id TEXT NOT NULL,
    local_version TEXT NOT NULL,  -- JSON
    remote_version TEXT NOT NULL,  -- JSON
    resolution TEXT DEFAULT 'manual',
    resolved_at TEXT,
    created_at TEXT NOT NULL
);
```

---

## 11. Implementation Checklist

| 任务 | 状态 |
|------|------|
| Version Vector | ✅ 完成（本文档） |
| Device ID in Events | ✅ 已有 |
| Merge Strategy | ✅ 完成（本文档） |
| Conflict Event | ✅ 完成（本文档） |
| Sync Protocol | ✅ 完成（本文档） |
| Conflict Resolution 文档 | ✅ 完成（本文档） |
| 两设备测试计划 | ✅ 完成（本文档） |
| Swift 实现 | ⏳ 待实现 |
| Python 实现 | ⏳ 待实现 |
| 两设备真实测试 | ⏳ 30天测试 |

---

## 12. SDK Notes

**V5 阶段不开放 SDK**

等待：
- 两设备测试完成（30天）
- 冲突解决策略稳定
- 协议验证无误

之后再开放 SDK。

---

*Specification Complete - 2026-03-02 21:40*
*银月，器灵 🌙*
