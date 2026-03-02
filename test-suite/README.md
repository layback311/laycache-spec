# LayCache Test Data - Reference Implementation
# ================================================
# 标准测试数据集，用于验证LayCache实现的一致性

TestDataSet:
  name: "LayCache Reference Test Data v1.0"
  description: "标准测试数据，用于验证实现是否符合协议规范"
  createdAt: "2026-03-02T21:00:00Z"
  createdBy: "银月 (器灵)"

---

## Events (5条)

### Event 1: User Preference
```json
{
  "eventId": "evt_001",
  "type": "user.preference",
  "content": {
    "category": "communication",
    "key": "style",
    "value": "concise"
  },
  "timestamp": "2026-03-01T10:00:00Z",
  "deviceId": "dev_test01",
  "previousHash": null
}
```

### Event 2: Task Created
```json
{
  "eventId": "evt_002",
  "type": "task.created",
  "content": {
    "taskId": "task_abc123",
    "title": "测试LayCache协议",
    "priority": "P0",
    "tags": ["test", "laycache"]
  },
  "timestamp": "2026-03-01T11:00:00Z",
  "deviceId": "dev_test01",
  "previousHash": "a1b2c3d4e5f6g7h8"
}
```

### Event 3: Task Completed
```json
{
  "eventId": "evt_003",
  "type": "task.completed",
  "content": {
    "taskId": "task_abc123",
    "completedAt": "2026-03-01T15:30:00Z",
    "notes": "所有测试通过"
  },
  "timestamp": "2026-03-01T15:30:00Z",
  "deviceId": "dev_test01",
  "previousHash": "b2c3d4e5f6g7h8i9"
}
```

### Event 4: Decision Made
```json
{
  "eventId": "evt_004",
  "type": "decision.made",
  "content": {
    "decisionId": "dec_xyz789",
    "topic": "选择加密算法",
    "choice": "Ed25519",
    "reason": "高效、安全、广泛支持",
    "alternatives": ["RSA", "ECDSA"]
  },
  "timestamp": "2026-03-02T09:00:00Z",
  "deviceId": "dev_test01",
  "previousHash": "c3d4e5f6g7h8i9j0"
}
```

### Event 5: Note Created
```json
{
  "eventId": "evt_005",
  "type": "note.created",
  "content": {
    "noteId": "note_qwe456",
    "title": "LayCache设计原则",
    "body": "可迁移、可验证、可审计、反锁定",
    "tags": ["design", "principles"]
  },
  "timestamp": "2026-03-02T10:00:00Z",
  "deviceId": "dev_test01",
  "previousHash": "d4e5f6g7h8i9j0k1"
}
```

---

## Derivations (2条)

### Derivation 1: AI Classification
```json
{
  "derivationId": "deriv_001",
  "eventId": "evt_002",
  "type": "classification",
  "modelId": "glm-5",
  "output": {
    "category": "work",
    "priority": "high",
    "sentiment": "neutral",
    "confidence": 0.95
  },
  "timestamp": "2026-03-01T11:05:00Z"
}
```

### Derivation 2: AI Summary
```json
{
  "derivationId": "deriv_002",
  "eventId": "evt_005",
  "type": "summary",
  "modelId": "glm-5",
  "output": {
    "summary": "记录了LayCache的四个核心设计原则：可迁移、可验证、可审计、反锁定",
    "keywords": ["LayCache", "设计原则", "可迁移", "可验证"]
  },
  "timestamp": "2026-03-02T10:05:00Z"
}
```

---

## Commits (2条)

### Commit 1: Initial Block
```json
{
  "commitId": "commit_001",
  "blockId": "block_aaa111",
  "previousCommitId": null,
  "changes": [
    {
      "action": "create",
      "entity": "event",
      "entityId": "evt_001",
      "timestamp": "2026-03-01T10:00:00Z"
    }
  ],
  "timestamp": "2026-03-01T10:00:00Z",
  "deviceId": "dev_test01",
  "commitHash": "hash_111aaa"
}
```

### Commit 2: Add Task
```json
{
  "commitId": "commit_002",
  "blockId": "block_aaa111",
  "previousCommitId": "commit_001",
  "changes": [
    {
      "action": "create",
      "entity": "event",
      "entityId": "evt_002",
      "timestamp": "2026-03-01T11:00:00Z"
    }
  ],
  "timestamp": "2026-03-01T11:00:00Z",
  "deviceId": "dev_test01",
  "commitHash": "hash_222bbb"
}
```

---

## Test Cases

### Test Case 1: Schema Validation
- **输入**: 上述5个Events
- **验证**: 每个Event是否符合Event Schema
- **预期**: 全部通过

### Test Case 2: Canonicalization
- **输入**: `{"b": 2, "a": 1}`
- **验证**: 标准化后是否为 `{"a":1,"b":2}`
- **预期**: 是

### Test Case 3: Hash Chain
- **输入**: 5个Events（包含previousHash）
- **验证**: previousHash是否正确
- **预期**: 全部匹配

### Test Case 4: Derivation Validation
- **输入**: 2个Derivations
- **验证**: 是否符合Derivation Schema
- **预期**: 全部通过

### Test Case 5: Commit Chain
- **输入**: 2个Commits
- **验证**: previousCommitId链是否正确
- **预期**: 全部匹配

---

## Expected Results

| 测试项 | 预期结果 |
|--------|----------|
| Event Schema | ✅ 5/5 通过 |
| Derivation Schema | ✅ 2/2 通过 |
| Commit Schema | ✅ 2/2 通过 |
| Canonicalization | ✅ 3/3 通过 |
| Hash Chain | ✅ 通过 |
| Bundle Format | ✅ 通过 |

**总分**: 100/100

---

## Usage

```bash
# 1. 准备测试数据
mkdir test_impl
cp events.jsonl test_impl/
cp derivations.jsonl test_impl/
cp commits.jsonl test_impl/
cp manifest.json test_impl/

# 2. 运行测试
python3 conformance-test.py test_impl/

# 3. 查看报告
cat test_impl/conformance_report_*.json
```

---

*Test Data v1.0 - 2026-03-02*
*银月，器灵 🌙*
