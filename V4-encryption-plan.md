# V4 加密功能实现计划

> 创建时间: 2026-03-02
> 稡块: MemorySecurity.swift
> 优先级: P2

---

## 🎯 目标
为 LayCache 添加端到端加密，支持生物识别认证。

---

## 📋 功能需求

### 1. 加密层
- ✅ AES-256-GCM 加密
- ✅ 数据库字段加密
- ✅ 密钥派生（PBKDF2 / Argon2id）
- ✅ 密钥存储（Keychain）

### 2. 认证层
- ✅ Face ID 集成
- ✅ Touch ID 集成
- ✅ 生物识别 → 加密密钥

- ✅ 失败回退（密码输入）

### 3. UI 层
- ⚠️ 设置页面：启用/禁用加密
- ⚠️ 加密状态指示器
- ⚠️ 生物识别提示
- ⚠️ 错误处理

- ✅ 非加密用户界面

- ✅ 緻加Event时不强制加密
- ✅ 导出时可选加密/非加密

---

## 🔧 技术栈
| 组件 | 技术选择 | 理由 |
|------|---------|------|
| **加密** | CryptoKit | 系统级， 性能最优 |
| **存储** | Keychain | 系统级密钥存储 |
| **认证** | LocalAuthentication | Face ID / Touch ID |
| **算法** | AES-256-GCM | 行业标准， 安全可靠 |
| **密钥派生** | PBKDF2 (iOS 16+) | 系统支持， 性能好 |

---

## 📊 数据流
### 加密流程
```
用户输入内容
     ↓
[未加密] 存储到 SQLite
     ↓
用户启用加密
     ↓
Face ID 验证
     ↓
派生加密密钥（从密码 + salt）
     ↓
加密内容（AES-256-GCM）
     ↓
存储密文 + nonce + tag
```

### 解密流程
```
用户打开内容
     ↓
Face ID 验证
     ↓
从 Keychain 获取密钥
     ↓
解密内容（AES-256-GCM）
     ↓
显示明文
```

---

## 🗂️ 数据库结构
### events 表
```sql
ALTER table events add column content_encrypted BLOB;
alter table events add column nonce BLOB;
alter table events add column tag BLOB;
alter table events add column salt TEXT;
alter table events add column key_derivation_method TEXT;
```

### 加密信息示例
```json
{
  "id": "a1b2c3d4...",
  "content": "加密后的内容（base64）",
  "nonce": "随机数（12字节）",
  "tag": "认证标签（16字节）",
  "salt": "密钥派生盐值",
  "key_derivation_method": "PBKDF2"
}
```

---

## 💻 实现步骤
### 阶段 1: 基础加密（1h）
- [ ] 实现 AES-256-GCM 加密/解密
- [ ] 实现 PBKDF2 密钥派生
- [ ] 单元测试
- [ ] 鷻加 `content_encrypted` 字段到数据库

### 阶段 2: Keychain 存储（1h）
- [ ] 实现密钥存储到 Keychain
- [ ] 从 Keychain 读取密钥
- [ ] 密钥删除（重置加密时）
- [ ] 错误处理

### 阶段 3: LocalAuthentication（1h）
- [ ] 集成 Face ID
- [ ] 集成 Touch ID
- [ ] 失败处理（密码回退）
- [ ] 测试在不同设备上
- [ ] 测试无生物识别设备

### 阶段 4: UI 集成（1h）
- [ ] 设置页面：加密开关
- [ ] 加密状态指示器
- [ ] 生物识别提示
- [ ] 错误提示

### 阶段 5: 数据迁移（0.5h）
- [ ] 非加密 → 加密迁移脚本
- [ ] 用户确认
- [ ] 备份提示

### 阶段 6: 导出支持（0.5h）
- [ ] 导出时选择加密/非加密
- [ ] 加密导出（需要密码）
- [ ] 非加密导出（当前方案）

---

## 🧪 关键代码
### AES-256-GCM 加密
```swift
import CryptoKit

func encrypt(content: String, key: SymmetricKey) -> (ciphertext: Data, nonce: Data, tag: Data) {
    let sealedBox = try! AES.GCM.seal(key: key, combining: .concat(nonce, tag)) {
        return try! sealedBox.seal(content.data(using: .utf8)!)
    }
}
    return (ciphertext, sealedBox.nonce, sealedBox.tag)
}
```

### 密钥派生
```swift
import CryptoKit

func deriveKey(password: String, salt: Data) -> SymmetricKey {
    let inputKeyMaterial = PBKDF2(
        password: password.data(using: .utf8)!,
        salt: salt,
        outputByteCount: 32
    )
    return SymmetricKey(data: inputKeyMaterial)
}
```
```

### Face ID 集成
```swift
import LocalAuthentication

func authenticateWithBiometrics() async throws -> Bool {
    let context = LAContext()
    var error: NSError?

    let result = try await context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)

    switch result {
    case .success:
        return true
    case .failure:
        throw AuthenticationError.failed
    case .fallback:
        // 回退到密码输入
        return false
    @unknown default:
        throw AuthenticationError.unknown
    }
}
```
```
---

## ⚠️ 安全考虑
### 1. 密钥管理
- ✅ 密钥存储在 Keychain（系统级）
- ✅ 密钥不存储在数据库中
- ✅ 密钥不记录在日志中
- ✅ 用户密码不存储（只用于派生）

### 2. 数据安全
- ✅ 明文内容只存在于内存中
- ✅ 数据库只存储密文
- ✅ 导出时提示用户加密
- ✅ 敏感内容强制本地处理

### 3. 认证安全
- ✅ Face ID 优先（用户友好）
- ✅ 密码作为回退（兼容性）
- ✅ 认证失败不显示内容
- ✅ 多次失败锁定（安全）

---

## 📊 测试计划
### 单元测试
- [ ] 加密/解密正确性
- [ ] 密钥派生一致性
- [ ] Face ID 成功/失败场景
- [ ] Touch ID 成功/失败场景
- [ ] 密码验证
- [ ] 错误处理

- [ ] 边界情况（空内容、超长内容）

### 集成测试
- [ ] 端到端加密流程
- [ ] 生物识别 → 加密 → 存储
- [ ] 读取 → 解密 → 显示
- [ ] 设置页面开关加密
- [ ] 导出加密/非加密
- [ ] 多设备同步（未来）

### 性能测试
- [ ] 加密性能（1000 次/秒）
- [ ] 解密性能
- [ ] 密钥派生性能
- [ ] Face ID 响应时间
- [ ] 内存占用

---

## 🚨 鸿沟事项
### 问题 1: 忘记密码
**影响:** 无法解密已加密内容

**解决方案:**
- ⚠️ 警告用户：忘记密码将无法恢复数据
- ⚠️ 建议用户使用 iCloud Keychain（生物识别）
- ⚠️ 提供"忘记密码"功能（重置加密）
- ⚠️ 重置后数据丢失提示
- ⚠️ 建议用户导出备份后再启用加密

### 问题 2: 设备丢失
**影响:** 无法访问加密数据

**解决方案:**
- ⚠️ 提示用户导出备份
- ⚠️ 新设备需要重新设置密码
- ⚠️ 无法恢复旧设备数据（没有备份）
- ⚠️ 建议用户定期导出到云端

### 问题 3: Face ID 不可用
**影响:** 无法使用生物识别

**解决方案:**
- ✅ 回退到密码输入
- ✅ 保持加密功能可用
- ⚠️ 提示用户使用密码
- ⚠️ 建议用户设置 Face ID

---

## 📅 时间表
| 日期 | 任务 | 预计时间 |
|------|------|---------|
| 2026-03-03 | 阶段 1: 基础加密 | 1h |
| 2026-03-04 | 阶段 2: Keychain | 1h |
| 2026-03-05 | 阶段 3: LocalAuthentication | 1h |
| 2026-03-06 | 阶段 4: UI 集成 | 1h |
| 2026-03-07 | 阶段 5: 数据迁移 | 0.5h |
| 2026-03-08 | 阶段 6: 导出支持 | 0.5h |
| 2026-03-09 | 集成测试 + Bug 修复 | 2h |
| **总计** | **7h**

---

## ✅ 鉊军指标
- 功能完整性: 100%
- 测试覆盖率: >90%
- 安全性: Keychain + AES-256-GCM
- 用户体验: Face ID 优先
- 兼容性: 密码回退
- 性能: 加密 < 100ms

- 文档完整性: 100%

---

*此计划遵循"先设计后实现"原则*
