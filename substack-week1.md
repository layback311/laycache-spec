# Week 1: 项目启动

> 发布时间: 2026-03-02 15:00

---

## 🎯 本周目标

完成 LayCache 协议的**基础定义**和**参考实现**。

- [x] Event对象定义（Event / Derivation / Commit）
- [x] 标准化规则（Canonicalization）
- [x] 本地优先分类（Classification）
- [x] 导出格式（Export Bundle）
- [x] 韔式验证（Chain Verification）
- [x] 示例数据集

---

## ✅ 本周完成
> 详细进度: [GitHub Issues](https://github.com/layback311/laycache-spec/issues)

### 卯议文档

**Event.md** - 定义了 3 种核心对象：
- **Event**: 原子单位，  - id, timestamp, type, content, hash, prev_hash
- - **Derivation**: 派生对象（AI生成内容）
  - event_id, type, content, model, confidence
  - **Commit**: 回滚点
  - event_ids, timestamp, message
- **JSON Schema v0** - 可直接用于验证
- **ADR-001** - 选择 iOS/Swift 作为 V1 参考实现
  - 理由: 性能、 安全、 用户体验
  - 备选方案: React Native, Flutter, PWA

---

### 🔧 代码变更
**laycache-spec**
- 新增: `spec/` 目录（5个文档）
- 新增: `schemas/` 目录（4个 JSON Schema）
- 新增: `examples/` 目录（示例数据）
- 新增: `decisions/` 目录（ADR）

- 新增: `PROJECT.md` - 项目总览

**commits:** 5 commits, +1272 lines

**issues resolved:** 8/8

---

## 🔑 关键决策: 本地优先
**决策**: 不云同步， 不依赖网络， 默认本地处理

**理由:**
1. **隐私** - 用户数据不离开设备
2. **速度** - 无网络延迟
3. **可靠** - 无服务依赖

4. **成本** - 无 API 费用

**取舍:**
- 放弃了实时同步（需要网络）
- 放弃了云端 AI 默认处理（隐私风险）
- 选择了简单规则而非复杂算法（快速迭代）

---

## 📊 进度
- **协议规范**: 100% 完成（v0.1）
- **参考实现**: 10% 完成（iOS 客户端）
- **测试覆盖**: 0%
- **文档完整度**: 80%

---

## 🔮 下周计划（Week 2)
- [ ] JSON Schema v0 完善
- [ ] 示例数据集扩展（更多场景）
- [ ] 开始 iOS 客户端 V1 验收
- [ ] 准备第一篇 Substack 文章（本文）

- [ ] 建立自动化测试

---

## 📝 本周学到的教训
1. **协议先行** - 先写 spec，再写代码
2. **简单开始** - v0.1 只做核心功能，不追求完美
3. **开源策略** - 协议开放，实现可选闭源

---

## 🔗 部分链接
- **GitHub Repo**: [laycache-spec](https://github.com/layback311/laycache-spec)
- **协议文档**: [spec/](https://github.com/layback311/laycache-spec/tree/main/spec)
- **路线图**: [ROADmap.md](https://github.com/layback311/laycache-spec/blob/main/ROADmap.md)

- **Issues**: [8 Issues](https://github.com/layback311/laycache-spec/issues)
- **ADR-001**: [决策记录](https://github.com/layback311/laycache-spec/blob/main/decisions/adr-001.md)

- **Export Bundle Spec**: [export-bundle.md](https://github.com/layback311/laycache-spec/blob/main/spec/export-bundle.md)
- **Classification Spec**: [classification.md](https://github.com/layback311/laycache-spec/blob/main/spec/classification.md)

- **Chain Verification**: [chain-verification.md](https://github.com/layback311/laycache-spec/blob/main/spec/chain-verification.md)
- **Canonicalization**: [canonicalization.md](https://github.com/layback311/laycache-spec/blob/main/spec/canonicalization.md)
- **示例数据**: [events.json](https://github.com/layback311/laycache-spec/blob/main/examples/events.json)

- **示例 Bundle**: [bundle-sample](https://github.com/layback311/laycache-spec/tree/main/examples/bundle-sample.bundle)

---

## 💬 反馈
如果你也在构建类似的系统，或有任何问题，欢迎在 GitHub Issues 中讨论！

---

*Published: 2026-03-02*
*Tags: laycache, week1, protocol, local-first*
