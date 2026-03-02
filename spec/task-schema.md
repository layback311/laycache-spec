# LayCache V3 - Task Schema Specification

> **Version:** 1.0.0 (Frozen)
> **Date:** 2026-03-02
> **Author:** 银月 (器灵)
> **Status:** 🔒 FROZEN - 不可修改核心字段

---

## 1. Overview

V3 引入 Task 对象，用于管理用户的待办事项、项目和目标。

**核心原则：**
- Task 变更通过 task_event 记录（append-only）
- 回滚 = 生成反向 commit（不可删除历史）
- 通知仅本地（不引入远程依赖）

---

## 2. Task Object Schema

### 2.1 Core Fields (Frozen)

```json
{
  "taskId": "task_abc123",
  "title": "测试LayCache协议",
  "status": "pending",
  "due": "2026-03-05T18:00:00Z",
  "priority": "P0",
  "sourceRefs": ["evt_001", "evt_002"],
  "createdAt": "2026-03-01T10:00:00Z",
  "updatedAt": "2026-03-02T21:20:00Z",
  "deviceId": "dev_abc123"
}
```

### 2.2 Field Definitions

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **taskId** | string | ✅ | 唯一标识符，格式：`task_<uuid>` |
| **title** | string | ✅ | 任务标题（1-500字符） |
| **status** | enum | ✅ | pending / in_progress / completed / cancelled |
| **due** | string | ❌ | ISO8601时间戳，null表示无截止日期 |
| **priority** | enum | ❌ | P0 / P1 / P2 / P3，默认P2 |
| **sourceRefs** | array | ❌ | 关联的event ID列表 |
| **createdAt** | string | ✅ | 创建时间（ISO8601） |
| **updatedAt** | string | ✅ | 最后更新时间（ISO8601） |
| **deviceId** | string | ✅ | 创建设备ID |

### 2.3 Status Enum

| 值 | 说明 | 可转换到 |
|---|------|---------|
| **pending** | 待处理 | in_progress, cancelled |
| **in_progress** | 进行中 | pending, completed, cancelled |
| **completed** | 已完成 | (终态) |
| **cancelled** | 已取消 | pending |

---

## 3. Task Event Schema

### 3.1 Event Types

| eventType | 说明 | 必填字段 |
|-----------|------|---------|
| **task.created** | 创建任务 | taskId, title, status |
| **task.updated** | 更新任务 | taskId, changes |
| **task.status_changed** | 状态变更 | taskId, oldStatus, newStatus |
| **task.completed** | 完成任务 | taskId, completedAt |
| **task.cancelled** | 取消任务 | taskId, reason |
| **task.rollback** | 回滚操作 | taskId, rollbackTo, rollbackCommitId |

### 3.2 Task Event Example

```json
{
  "eventId": "evt_task_001",
  "eventType": "task.created",
  "taskId": "task_abc123",
  "content": {
    "title": "测试LayCache协议",
    "status": "pending",
    "priority": "P0",
    "due": "2026-03-05T18:00:00Z"
  },
  "timestamp": "2026-03-01T10:00:00Z",
  "deviceId": "dev_abc123",
  "commitId": "commit_001"
}
```

### 3.3 Append-Only Rule

**规则：**
- Task Event 一旦写入，**永远不可删除或修改**
- 所有变更通过新的 task_event 记录
- 历史完整保留，可审计

---

## 4. Rollback Semantics

### 4.1 Definition

**回滚 ≠ 删除历史**

回滚 = 生成一个反向 commit，记录"撤销"操作

### 4.2 Rollback Process

```
1. 用户请求回滚到 commit_A
2. 系统找到 commit_A 之后的所有 commits
3. 按时间倒序生成反向操作
4. 写入新的 rollback commit
5. 更新 task 状态
```

### 4.3 Rollback Event Example

```json
{
  "eventId": "evt_rollback_001",
  "eventType": "task.rollback",
  "taskId": "task_abc123",
  "content": {
    "rollbackTo": "commit_001",
    "rollbackFrom": "commit_003",
    "reversedCommits": ["commit_003", "commit_002"],
    "reason": "误操作"
  },
  "timestamp": "2026-03-02T21:20:00Z",
  "deviceId": "dev_abc123",
  "commitId": "commit_rollback_001"
}
```

### 4.4 Rollback Rules

| 规则 | 说明 |
|------|------|
| **不可删除历史** | 所有 commits 保留，包括 rollback |
| **可重复回滚** | 可以回滚到任意历史 commit |
| **链式记录** | rollback commit 链接到原 commit |
| **幂等性** | 多次回滚到同一 commit，结果一致 |

---

## 5. Conflict Behavior (Single Device)

### 5.1 Current Scope

**V3 仅支持单设备，不处理跨设备冲突**

### 5.2 Single Device Conflicts

| 冲突类型 | 处理方式 |
|---------|---------|
| 并发更新同一字段 | 后写入覆盖（时间戳排序） |
| 状态冲突 | 状态机验证，拒绝非法转换 |
| 引用不存在event | 写入警告日志，task仍创建 |

### 5.3 Future: Multi-Device (V5)

V5 将引入：
- Version Vector
- Conflict Event
- 三路合并策略

---

## 6. Notification Layer

### 6.1 Scope

**V3 通知仅限本地，不引入远程依赖**

### 6.2 Notification Types

| 类型 | 触发条件 |
|------|---------|
| **task.due_reminder** | 任务即将到期（提前1h/1d） |
| **task.status_changed** | 任务状态变更 |
| **task.rollback** | 回滚操作完成 |

### 6.3 Notification Storage

```json
{
  "notificationId": "notif_001",
  "type": "task.due_reminder",
  "taskId": "task_abc123",
  "message": "任务'测试LayCache协议'将在1小时后到期",
  "scheduledAt": "2026-03-05T17:00:00Z",
  "deliveredAt": null,
  "deviceId": "dev_abc123"
}
```

---

## 7. SQL Schema

### 7.1 Tasks Table

```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    due TEXT,
    priority TEXT DEFAULT 'P2',
    source_refs TEXT,  -- JSON array
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    device_id TEXT NOT NULL
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due);
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

### 7.2 Task Events Table

```sql
CREATE TABLE task_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    task_id TEXT NOT NULL,
    content TEXT NOT NULL,  -- JSON
    timestamp TEXT NOT NULL,
    device_id TEXT NOT NULL,
    commit_id TEXT NOT NULL,
    previous_hash TEXT
);

CREATE INDEX idx_task_events_task ON task_events(task_id);
CREATE INDEX idx_task_events_timestamp ON task_events(timestamp);
```

### 7.3 Notifications Table

```sql
CREATE TABLE notifications (
    notification_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    task_id TEXT,
    message TEXT NOT NULL,
    scheduled_at TEXT,
    delivered_at TEXT,
    device_id TEXT NOT NULL
);

CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at);
```

---

## 8. API Reference

### 8.1 Create Task

```swift
func createTask(
    title: String,
    status: TaskStatus = .pending,
    priority: TaskPriority = .P2,
    due: Date? = nil,
    sourceRefs: [String]? = nil
) -> Task
```

### 8.2 Update Task

```swift
func updateTask(
    taskId: String,
    changes: [String: Any]
) -> Task
```

### 8.3 Rollback Task

```swift
func rollbackTask(
    taskId: String,
    toCommitId: String,
    reason: String? = nil
) -> Task
```

### 8.4 Get Task History

```swift
func getTaskHistory(taskId: String) -> [TaskEvent]
```

---

## 9. Test Cases

### 9.1 Rollback Test

```swift
func testRollback() {
    // 1. 创建任务
    let task = createTask(title: "Test")
    
    // 2. 更新任务（commit_1）
    updateTask(taskId: task.id, changes: ["status": "in_progress"])
    
    // 3. 再次更新（commit_2）
    updateTask(taskId: task.id, changes: ["priority": "P0"])
    
    // 4. 回滚到 commit_1
    rollbackTask(taskId: task.id, toCommitId: "commit_1")
    
    // 5. 验证
    XCTAssert(task.status == "in_progress")  // commit_1 的状态
    XCTAssert(task.priority == "P2")         // 回滚了 commit_2 的优先级
    XCTAssert(getTaskHistory(task.id).count == 4)  // created + update + update + rollback
}
```

### 9.2 Status Machine Test

```swift
func testStatusTransitions() {
    let task = createTask(title: "Test", status: .pending)
    
    // 合法转换
    XCTAssertNoThrow(updateTask(taskId: task.id, changes: ["status": "in_progress"]))
    
    // 非法转换：completed 不能转回 pending
    updateTask(taskId: task.id, changes: ["status": "completed"])
    XCTAssertThrowsError(updateTask(taskId: task.id, changes: ["status": "pending"]))
}
```

---

## 10. Implementation Checklist

| 任务 | 状态 | 说明 |
|------|------|------|
| Task Schema 冻结 | ✅ 完成 | 本文档 |
| SQL Schema | ✅ 完成 | 本文档 |
| Task Events Schema | ✅ 完成 | 本文档 |
| Rollback 实现 | ⏳ 待实现 | Swift/Python |
| 通知层实现 | ⏳ 待实现 | 本地通知 |
| Conflict 文档 | ✅ 完成 | 本文档 |
| 回滚测试用例 | ✅ 完成 | 本文档 |

---

## 11. Frozen Commitment

**🔒 V3 Task Schema 已冻结**

以下内容不可修改：
- Task 核心字段（taskId, title, status, due, priority, sourceRefs）
- Task Event 类型定义
- 回滚语义（反向commit）

允许扩展：
- 新增可选字段
- 新增 event 类型
- 优化实现细节

---

*Schema Frozen - 2026-03-02 21:20*
*银月，器灵 🌙*
