# LayCache V4 - Encryption & Principal Specification

> **Version:** 1.0.0
> **Date:** 2026-03-02
> **Author:** 银月 (器灵)

---

## 1. Overview

V4 把"可信"升级为"私有主权"，引入加密和身份抽象层。

**核心原则：**
- 加密是可选的（向后兼容）
- 加密不影响导出结构
- 密钥由用户控制，不离开设备
- 加密模块可插拔

---

## 2. Principal Abstraction

### 2.1 Principal Object

```json
{
  "principalId": "principal_abc123",
  "deviceId": "dev_xyz789",
  "authMethod": "biometric",
  "createdAt": "2026-03-02T21:35:00Z",
  "lastAuthenticated": "2026-03-02T21:40:00Z"
}
```

### 2.2 Fields

| 字段 | 类型 | 说明 |
|------|------|------|
| **principalId** | string | 主体唯一标识符 |
| **deviceId** | string | 关联的设备ID |
| **authMethod** | enum | biometric / passcode / none |
| **createdAt** | string | 创建时间 |
| **lastAuthenticated** | string | 最后认证时间 |

### 2.3 Auth Methods

| Method | 说明 | 安全级别 |
|--------|------|---------|
| **biometric** | Face ID / Touch ID | 高 |
| **passcode** | 设备密码 | 中 |
| **none** | 无认证 | 低 |

---

## 3. Device Master Key

### 3.1 Key Generation

```
1. 生成 256-bit 主密钥（随机）
2. 存储在 Secure Enclave / Keychain
3. 派生 per-block 密钥（HKDF）
4. 密钥永不离开设备
```

### 3.2 Key Derivation (HKDF)

```
block_key = HKDF-SHA256(
    master_key,
    salt = block_id,
    info = "laycache-block-encryption",
    length = 32
)
```

### 3.3 Key Storage

| 平台 | 存储位置 | 访问控制 |
|------|---------|---------|
| **iOS** | Keychain (Secure Enclave) | 仅App可访问 |
| **macOS** | Keychain | 需用户授权 |
| **Python** | OS Keyring | 系统密码管理 |

---

## 4. Encryption Module

### 4.1 Encryption Algorithm

**AES-256-GCM**

| 参数 | 值 |
|------|---|
| 算法 | AES-256-GCM |
| 密钥长度 | 256 bits |
| IV长度 | 96 bits |
| Tag长度 | 128 bits |

### 4.2 Encrypted Data Format

```json
{
  "encrypted": true,
  "algorithm": "AES-256-GCM",
  "iv": "base64_encoded_iv",
  "ciphertext": "base64_encoded_ciphertext",
  "tag": "base64_encoded_tag",
  "keyId": "key_abc123"
}
```

### 4.3 Pluggable Encryption

```swift
protocol EncryptionProvider {
    func encrypt(data: Data, keyId: String) throws -> EncryptedData
    func decrypt(encrypted: EncryptedData, keyId: String) throws -> Data
    func generateKey() throws -> String
}

// 默认实现：AES-256-GCM
class AESGCMEncryptionProvider: EncryptionProvider {
    // ...
}

// 可插拔：用户可自定义
class CustomEncryptionProvider: EncryptionProvider {
    // ...
}
```

---

## 5. Encrypted Events

### 5.1 Event Encryption

```json
{
  "eventId": "evt_001",
  "type": "user.preference",
  "content": {
    "encrypted": true,
    "algorithm": "AES-256-GCM",
    "iv": "...",
    "ciphertext": "...",
    "tag": "...",
    "keyId": "key_abc123"
  },
  "timestamp": "2026-03-02T21:35:00Z",
  "deviceId": "dev_xyz789"
}
```

### 5.2 Selective Encryption

**规则：**
- 可选择哪些字段加密
- eventId, timestamp, deviceId 不加密
- content 字段可加密

---

## 6. Export with Encryption

### 6.1 Encrypted Bundle

```
laycache_export.bundle/
├── manifest.json           # 未加密
├── events.jsonl           # 加密（如果启用）
├── commits.jsonl          # 未加密
├── blocks.jsonl           # 未加密
├── key_backup.encrypted   # 加密的密钥备份（可选）
└── signature.bin          # 签名
```

### 6.2 Key Backup

```json
{
  "keyBackupVersion": "1.0.0",
  "encryptedKey": "...",  // 用用户密码加密的主密钥
  "algorithm": "AES-256-GCM",
  "kdf": "PBKDF2-SHA256",
  "iterations": 100000,
  "salt": "..."
}
```

### 6.3 Export Behavior

| 场景 | 行为 |
|------|------|
| **未加密模式** | 正常导出，events未加密 |
| **加密模式 + 无密钥备份** | 导出加密events，需原设备解密 |
| **加密模式 + 密钥备份** | 可在其他设备导入（需密码） |

---

## 7. Backwards Compatibility

### 7.1 Test Mode

```swift
// 未加密模式（测试/兼容）
LayCacheDB(encryptionEnabled: false)

// 加密模式（生产）
LayCacheDB(encryptionEnabled: true)
```

### 7.2 Migration

```
1. 检测旧数据库（未加密）
2. 提示用户启用加密
3. 重新加密所有events（可选）
4. 保留未加密的历史（向后兼容）
```

---

## 8. SQL Schema

### 8.1 Principals Table

```sql
CREATE TABLE principals (
    principal_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    auth_method TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_authenticated TEXT
);
```

### 8.2 Keys Table

```sql
CREATE TABLE encryption_keys (
    key_id TEXT PRIMARY KEY,
    principal_id TEXT NOT NULL,
    algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
    created_at TEXT NOT NULL,
    key_data BLOB  -- 加密存储
);
```

---

## 9. Security Considerations

### 9.1 Threat Model

| 威胁 | 缓解措施 |
|------|---------|
| 设备被盗 | Secure Enclave + 生物认证 |
| 备份泄露 | 密钥备份用强密码加密 |
| 暴力破解 | PBKDF2 100,000 iterations |
| 中间人攻击 | 本地加密，不依赖网络 |

### 9.2 Best Practices

- 使用系统提供的 Secure Enclave
- 密钥永不离开设备
- 使用强密码（如果启用密钥备份）
- 定期轮换密钥（可选）

---

## 10. Implementation Checklist

| 任务 | 状态 |
|------|------|
| Principal 抽象 | ✅ 完成（本文档） |
| Key Derivation 方案 | ✅ 完成（本文档） |
| 加密模块接口 | ✅ 完成（本文档） |
| Encrypted Event 格式 | ✅ 完成（本文档） |
| Export 加密支持 | ✅ 完成（本文档） |
| Backwards Compatibility | ✅ 完成（本文档） |
| Swift 实现 | ⏳ 待实现 |
| Python 实现 | ⏳ 待实现 |
| 测试用例 | ⏳ 待实现 |

---

*Specification Complete - 2026-03-02 21:35*
*银月，器灵 🌙*
