# Export Bundle v0.1

> 导出格式规范 - 支持跨设备迁移

---

## 概述

Export Bundle 是 LayCache 的**完整快照**，包含：
- 所有 Event
- 所有 Derivation
- 所有 Commit
- 元数据

---

## Bundle 结构

### 文件格式

```
laycache-export-YYYYMMDD-HHMMSS.bundle/
├── manifest.json           # 元数据
├── events/                 # Event目录
│   ├── 0001.json
│   ├── 0002.json
│   └── ...
├── derivations/            # Derivation目录
│   ├── 0001.json
│   └── ...
├── commits/                # Commit目录
│   ├── 0001.json
│   └── ...
└── signatures/             # 签名目录（可选）
    ├── manifest.sig
    └── events.sig
```

---

## Manifest Schema

### 字段定义

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `version` | string | ✅ | 协议版本（如"0.1"） |
| `exported_at` | ISO8601 | ✅ | 导出时间戳 |
| `device_id` | string | ✅ | 导出设备ID |
| `event_count` | integer | ✅ | Event数量 |
| `derivation_count` | integer | ✅ | Derivation数量 |
| `commit_count` | integer | ✅ | Commit数量 |
| `chain_head_hash` | string | ✅ | Event链头hash |
| `encryption` | object | ❌ | 加密信息 |
| `checksum` | string | ✅ | Bundle校验和 |

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://laycache.dev/schemas/export-manifest-v0.json",
  "title": "LayCache Export Manifest v0",
  "type": "object",
  "required": [
    "version",
    "exported_at",
    "device_id",
    "event_count",
    "derivation_count",
    "commit_count",
    "chain_head_hash",
    "checksum"
  ],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$",
      "description": "协议版本"
    },
    "exported_at": {
      "type": "string",
      "format": "date-time",
      "description": "导出时间戳（UTC）"
    },
    "device_id": {
      "type": "string",
      "description": "导出设备ID"
    },
    "event_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Event数量"
    },
    "derivation_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Derivation数量"
    },
    "commit_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Commit数量"
    },
    "chain_head_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "Event链头hash（最新Event）"
    },
    "encryption": {
      "type": "object",
      "properties": {
        "algorithm": {
          "type": "string",
          "enum": ["AES-256-GCM", "none"]
        },
        "key_derivation": {
          "type": "string",
          "enum": ["PBKDF2", "Argon2id", "none"]
        },
        "encrypted": {
          "type": "boolean"
        }
      }
    },
    "checksum": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "Bundle SHA-256校验和"
    }
  }
}
```

---

## 完整示例

### manifest.json

```json
{
  "version": "0.1",
  "exported_at": "2026-03-02T14:30:00Z",
  "device_id": "dev_abc123def456",
  "event_count": 5,
  "derivation_count": 0,
  "commit_count": 0,
  "chain_head_hash": "d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f",
  "encryption": {
    "algorithm": "none",
    "key_derivation": "none",
    "encrypted": false
  },
  "checksum": "a1b2c3d4e5f6789012345678abcdef90a1b2c3d4e5f6789012345678abcdef90"
}
```

### events/0001.json

```json
{
  "id": "a1b2c3d4e5f6789012345678abcdef01",
  "timestamp": "2026-03-02T10:00:00Z",
  "type": "capture",
  "content": "明天下午3点开会",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "prev_hash": null,
  "device_id": "dev_abc123def456",
  "payload_encrypted": false
}
```

---

## Checksum 计算

### 方法1：递归SHA256（推荐）

```python
import hashlib
import json
from pathlib import Path

def compute_bundle_checksum(bundle_path: Path) -> str:
    """
    递归计算所有文件的SHA256
    """
    hasher = hashlib.sha256()

    # 按字母顺序遍历所有文件
    for file_path in sorted(bundle_path.rglob("*.json")):
        # 相对路径（标准化）
        rel_path = file_path.relative_to(bundle_path)
        hasher.update(str(rel_path).encode())

        # 文件内容
        with open(file_path, "rb") as f:
            hasher.update(f.read())

    return hasher.hexdigest()
```

### 方法2：Manifest哈希

```python
def compute_manifest_hash(manifest: dict) -> str:
    """
    仅计算manifest的hash（快速）
    """
    manifest_json = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(manifest_json.encode()).hexdigest()
```

**决策：** 使用**方法1**（递归SHA256），确保完整性。

---

## 导出流程

### 1. 创建Bundle目录

```python
from datetime import datetime
from pathlib import Path

timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
bundle_dir = Path(f"laycache-export-{timestamp}.bundle")
bundle_dir.mkdir()
(bundle_dir / "events").mkdir()
(bundle_dir / "derivations").mkdir()
(bundle_dir / "commits").mkdir()
(bundle_dir / "signatures").mkdir()
```

### 2. 导出Events

```python
def export_events(events: list, bundle_dir: Path):
    events_dir = bundle_dir / "events"

    for i, event in enumerate(events, 1):
        filename = f"{i:04d}.json"  # 0001.json, 0002.json, ...
        with open(events_dir / filename, "w") as f:
            json.dump(event, f, indent=2)
```

### 3. 生成Manifest

```python
def generate_manifest(events, derivations, commits, device_id):
    return {
        "version": "0.1",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "device_id": device_id,
        "event_count": len(events),
        "derivation_count": len(derivations),
        "commit_count": len(commits),
        "chain_head_hash": events[-1].hash if events else None,
        "encryption": {
            "algorithm": "none",
            "key_derivation": "none",
            "encrypted": False
        },
        "checksum": ""  # 稍后计算
    }
```

### 4. 计算Checksum并写入

```python
manifest = generate_manifest(events, derivations, commits, device_id)
checksum = compute_bundle_checksum(bundle_dir)
manifest["checksum"] = checksum

with open(bundle_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
```

---

## 导入流程

### 1. 验证Checksum

```python
def verify_bundle(bundle_path: Path) -> bool:
    # 读取manifest
    with open(bundle_path / "manifest.json") as f:
        manifest = json.load(f)

    # 重新计算checksum
    actual_checksum = compute_bundle_checksum(bundle_path)

    # 对比
    return actual_checksum == manifest["checksum"]
```

### 2. 验证Event链

```python
def verify_event_chain(events: list) -> tuple[bool, str]:
    """
    返回 (is_valid, error_event_id)
    """
    if not events:
        return True, None

    # 按timestamp排序
    events = sorted(events, key=lambda e: e["timestamp"])

    # 第一个Event必须没有prev_hash
    if events[0]["prev_hash"] is not None:
        return False, events[0]["id"]

    # 验证链式关系
    for i in range(1, len(events)):
        if events[i]["prev_hash"] != events[i-1]["hash"]:
            return False, events[i]["id"]

    return True, None
```

### 3. 合并到本地数据库

```python
def import_bundle(bundle_path: Path, db: LayCacheDB):
    # 验证
    if not verify_bundle(bundle_path):
        raise ValueError("Bundle checksum mismatch")

    # 导入Events
    events_dir = bundle_path / "events"
    for event_file in sorted(events_dir.glob("*.json")):
        with open(event_file) as f:
            event = json.load(f)
        db.insert_event(event)

    # 导入Derivations
    derivations_dir = bundle_path / "derivations"
    for derivation_file in sorted(derivations_dir.glob("*.json")):
        with open(derivation_file) as f:
            derivation = json.load(f)
        db.insert_derivation(derivation)

    # 导入Commits
    commits_dir = bundle_path / "commits"
    for commit_file in sorted(commits_dir.glob("*.json")):
        with open(commit_file) as f:
            commit = json.load(f)
        db.insert_commit(commit)
```

---

## 加密支持（V0.5）

### 加密流程

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_bundle(bundle_path: Path, password: str):
    # 1. 派生密钥（PBKDF2）
    salt = os.urandom(16)
    key = pbkdf2_hmac("sha256", password.encode(), salt, 100000, 32)

    # 2. 加密每个文件
    aesgcm = AESGCM(key)

    for json_file in bundle_path.rglob("*.json"):
        # 读取明文
        with open(json_file) as f:
            plaintext = f.read().encode()

        # 加密
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # 写入（格式：nonce + ciphertext）
        with open(json_file, "wb") as f:
            f.write(nonce + ciphertext)

    # 3. 更新manifest
    manifest = json.load(open(bundle_path / "manifest.json"))
    manifest["encryption"] = {
        "algorithm": "AES-256-GCM",
        "key_derivation": "PBKDF2",
        "encrypted": True,
        "salt": salt.hex()
    }
    json.dump(manifest, open(bundle_path / "manifest.json", "w"), indent=2)
```

---

## 版本兼容性

### v0.1 → v0.5

- ✅ 向后兼容（v0.5可读取v0.1）
- ✅ 新增`encryption`字段（可选）

### v0.5 → v1.0

- ✅ 向后兼容
- ✅ 新增`metadata`字段（可选）

---

## 安全考虑

### 1. 不导出敏感数据

```python
def is_safe_to_export(content: str) -> bool:
    """检查是否包含敏感信息"""
    sensitive_keywords = [
        "password",
        "api_key",
        "secret",
        "token",
        # 可扩展
    ]
    return not any(keyword in content.lower() for keyword in sensitive_keywords)
```

### 2. 用户确认

```swift
// iOS实现
func exportBundle() {
    // 1. 生成预览
    let preview = generateExportPreview()

    // 2. 用户确认
    showAlert(
        title: "导出数据",
        message: "将导出 \(preview.eventCount) 条记录，确定吗？",
        actions: [
            .cancel(),
            .default("导出") { [weak self] in
                self?.performExport()
            }
        ]
    )
}
```

### 3. 校验和验证

- ✅ 导出时自动计算
- ✅ 导入时强制验证
- ✅ 不匹配则拒绝导入

---

## 实现状态

| 项目 | 状态 | 位置 |
|------|------|------|
| Export Manifest Schema | ✅ 完成 | spec/export-bundle.md |
| JSON Schema | ⏳ 待创建 | schemas/export-manifest-v0.json |
| 示例Bundle | ⏳ 待创建 | examples/export-bundle/ |
| 导出逻辑（iOS） | ⏳ 待开发 | LayCacheExport.swift |
| 导入逻辑（iOS） | ⏳ 待开发 | LayCacheImport.swift |

---

*此文档解决Issue #4*
