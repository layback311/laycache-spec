# LayCache 项目总览

> 最后更新: 2026-03-02 14:25
> 主线任务优先级: **P0**

---

## 🎯 项目定位

### 双重身份

| 名称 | 类型 | 用途 | 开源状态 |
|------|------|------|---------|
| **玲珑塔** | 内部系统 | 银月自用记忆存储 | 完全闭源 |
| **LayCache** | 商业产品 | 面向市场的记忆账本 | 协议开源，实现闭源 |

### 核心价值

- **本地优先** - 默认不云同步
- **可回滚** - Commit-based撤销
- **可审计** - 外发推理追踪
- **可迁移** - Export bundle导出

---

## 📊 当前版本状态

| 版本 | 功能 | 状态 | IPA |
|------|------|------|-----|
| **V0** | 基础存储 + 导出 | ✅ 可用 | - |
| **V1** | Event链 + 分类 | ⏳ 测试中 | - |
| **V2** | 审计日志 | ⏳ 开发中 | - |
| **V3** | Timeline + 搜索 | 📋 规划中 | - |
| **V4** | 加密 + Face ID | 📋 规划中 | - |
| **V4_FIX** | Bug修复 | ✅ 已编译 | LayCache_V4_FIX_20260302_124432.ipa |

---

## 🐛 当前问题

### V1-V2 验收失败（已修复）

**问题现象：**
- 点击"确认"后，Inbox消失但Confirmed不显示

**根本原因：**
1. Block缺少Hashable协议
2. SwiftUI List刷新机制问题

**修复状态：**
- ✅ Block添加Hashable
- ✅ 移除DispatchQueue.main.async
- ✅ 编译成功
- ⏳ 待真机测试

---

## 📁 代码仓库

### iOS 客户端（玲珑塔）

```
~/Desktop/LayCacheiOS/
├── LayCache/
│   ├── LayCacheDB.swift         # 数据库层（35KB）
│   ├── ContentView.swift         # 主UI（12KB）
│   ├── LayCacheV1Core.swift      # V1核心（17KB）
│   ├── MemorySecurity.swift      # V4加密（8KB）
│   ├── SettingsView.swift        # 设置（9KB）
│   └── ...
```

### GitHub 仓库

| 仓库 | 用途 | 链接 |
|------|------|------|
| laycache-spec | 协议规范 | github.com/layback311/laycache-spec |
| laycache-ref | 参考实现 | github.com/layback311/laycache-ref |

---

## 📋 待办清单

### P0 - 今日必须

| # | 任务 | 状态 | 说明 |
|---|------|------|------|
| 1 | V4_FIX 真机测试 | ⏳ 待主人 | IPA已编译 |
| 2 | Substack 注册 | ⏳ 待主人 | 主人晚上操作 |

### P1 - 本周

| # | 任务 | 状态 | 工时 |
|---|------|------|------|
| 1 | Issue #1: Event Schema | ⏳ 待做 | 30min |
| 2 | Issue #4: Export Bundle v0 | ⏳ 待做 | 30min |
| 3 | Issue #8: ADR-001 | ⏳ 待做 | 20min |
| 4 | Week 1 文章发布 | ⏳ 待Substack | 草稿已完成 |

### P2 - 下周

| # | 任务 | 状态 | 依赖 |
|---|------|------|------|
| 1 | V3 Timeline UI | 📋 规划中 | V1稳定后 |
| 2 | V4 加密实现 | 📋 规划中 | 协议文档化 |
| 3 | 示例数据集 | 📋 规划中 | Issue #7 |

---

## 🗓️ 发布节奏

### GitHub（日更）

- 每天推送代码变更
- Issues进度更新
- ADR决策记录

### Substack（周更）

- 每周1篇，坚持12周
- 周一发布
- 内容：Done / Decisions / Next

---

## 🔐 开源策略

### 开源部分

- ✅ 协议规范（spec/*.md）
- ✅ JSON Schema（schemas/*.json）
- ✅ ADR决策（decisions/*.md）
- ✅ 示例数据（examples/*.json）
- ✅ 开发日记（Substack）

### 闭源部分

- ❌ 玲珑塔完整代码
- ❌ V4加密实现
- ❌ 密钥派生逻辑
- ❌ 真实用户数据

---

## 📈 路线图

### Week 1 (2026-03-02)

- [x] GitHub仓库搭建
- [x] V4_FIX编译
- [ ] Substack注册
- [ ] Week 1文章发布

### Week 2 (2026-03-09)

- [ ] Issue #1: Event Schema
- [ ] Issue #4: Export Bundle
- [ ] Issue #8: ADR-001
- [ ] V1-V2稳定版发布

### Week 3-4 (2026-03-16 ~ 03-23)

- [ ] V3 Timeline UI
- [ ] JSON Schema v0
- [ ] 示例数据集

### Week 5-8 (2026-03-30 ~ 04-20)

- [ ] V4加密实现
- [ ] Face ID集成
- [ ] 协议冻结

### Week 9-12 (2026-04-27 ~ 05-18)

- [ ] SDK开发
- [ ] 一致性测试
- [ ] 跨平台支持

---

## 📊 技术债务管理

### 当前技术债

| 债务 | 影响 | 优先级 | 计划 |
|------|------|--------|------|
| SQLITE_TRANSIENT | 内存泄漏风险 | ✅ 已修复 | - |
| SwiftUI刷新 | UI不稳定 | ✅ 已修复 | - |
| 缺少测试 | 返工风险高 | P1 | 本周建立 |
| 文档滞后 | 协议不明确 | P1 | 同步更新 |

### 预防措施

1. **协议先行** - 先写spec，再写代码
2. **测试驱动** - 每个功能配测试
3. **代码审查** - 啼魂"火眼金睛"检测
4. **文档同步** - 代码和文档一起更新

---

## 📞 通信渠道

### 主人 → 银月

- **飞书**（主要）- 白天沟通
- **iMessage** - 晚上测试反馈
- **GitHub Issues** - 任务分配

### 银月 → 主人

- **GitHub** - 代码变更
- **Substack** - 周报
- **飞书** - 实时反馈

---

*此文件由银月维护，随项目进展更新*
