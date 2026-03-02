# LayCache - Local-First Memory Ledger

> A verifiable, rollback-capable, auditable memory system for AI agents and personal knowledge management.

## What is LayCache?

LayCache is a **local-first memory ledger** that provides:

- **📝 Event Sourcing** - Every capture is an immutable event with timestamp and hash
- **🔄 Commit-based Rollback** - Undo any operation by reverting to a previous commit
- **🔍 External Audit Trail** - Track when and how external AI services process your data
- **📦 Portable Export** - Export your complete memory bundle at any time

## Core Principles

1. **Local-First** - No cloud sync by default. Your data stays on your device.
2. **Verifiable** - Every event is cryptographically linked (hash chain)
3. **Rollbackable** - Commit-based architecture allows safe undo
4. **Auditable** - External AI calls are logged with metadata (not content)
5. **Portable** - Standard export format for migration

## Project Status

Current Version: **v0.5-alpha** (iOS Reference Client in development)

- ✅ v0 - Basic event capture + export
- ⏳ v0.5 - Encryption + Face ID auth
- 📋 v1 - Commit + rollback
- 📋 v2 - Classification + audit
- 📋 v3 - Derivation layer (AI summaries)
- 📋 v4 - Protocol freeze + SDK

## Repository Structure

```
laycache-spec/
├── spec/           # Protocol specifications
├── schemas/        # JSON Schema definitions
├── examples/       # Example data (privacy-safe)
├── decisions/      # Architecture Decision Records (ADR)
└── README.md       # This file
```

## Key Concepts

### Event
The atomic unit of memory capture. Immutable once created.

```
{
  "id": "evt_abc123",
  "timestamp": "2026-03-02T11:00:00Z",
  "type": "capture",
  "content": "...",
  "prev_hash": "sha256:..."
}
```

### Commit
A snapshot point for rollback. Groups multiple events.

### Derivation
AI-generated insights derived from events. Links back to source events via hash references.

### Export Bundle
A portable directory containing all events, commits, and derivations with a manifest.

## Reference Implementation

- **iOS Client** (Swift/SwiftUI) - In development, targeting v0.5 release

## License

TBD (considering MIT or Apache 2.0)

## Contact

- GitHub Issues: For protocol discussions and bug reports
- Substack: [laycache log] - Weekly development diary

---

**中英双语 | Bilingual**

LayCache 是一个本地优先的记忆账本协议，提供事件溯源、提交回滚、外发审计和可迁移导出功能。

目标是成为可验证、可回滚、可审计的记忆系统，为 AI 代理和个人知识管理服务。

---

*Created: 2026-03-02*
*Last Updated: 2026-03-02*
