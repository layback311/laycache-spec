# LayCache Roadmap

## Version History

| Version | Status | Target Date | Description |
|---------|--------|------------|-------------|
| v0.1 | ✅ Done | 2026-02-28 | Basic event storage |
| v0.5 | ⏳ WIP | 2026-03-15 | V4 encryption + Face ID |
| v1.0 | 📋 Planned | 2026-04-01 | Complete inbox/classification |
| v2.0 | 📋 Planned | 2026-05-01 | Timeline view |
| v3.0 | 📋 Planned | 2026-06-01 | Search + filtering |
| v4.0 | 📋 Planned | 2026-07-01 | **Protocol Freeze** - Stable spec |
| v5.0+ | 🔮 Future | 2026-Q4 | SDK + consistency testing |

## Current Phase: v0.5 (WIP)

### In Progress
- [ ] V4 encryption implementation
- [ ] Face ID integration
- [ ] Export bundle v0 format

### Next Up (v1.0)
- [ ] Complete inbox workflow
- [ ] Block classification system
- [ ] Confirmed section stability

## Feature Breakdown by Version

### v0.1 ✅
- Event schema definition
- SQLite storage layer
- Basic CRUD operations
- Hash chain for events

### v0.5 ⏳
- AES-256-GCM encryption
- LocalAuthentication (Face ID/Touch ID)
- Export bundle (JSON + attachments)
- Import from bundle

### v1.0 📋
- Inbox inbox section
- Classification metadata
- Timeline view
- Search functionality

### v2.0 📋
- Complete timeline view
- Filtering by type/date
- Export filtered subsets
- AI-generated summaries

### v3.0 📋
- Full-text search
- Advanced filtering
- Batch operations
- Performance optimization

### v4.0 📋
- **Protocol Freeze** - No breaking changes
- Complete documentation
- Reference implementation
- JSON Schema finalization

### v5.0+ 🔮
- Public SDK for third-party implementations
- Consistency test suite
- Cross-platform support
- Plugin architecture

## Non-Goals (What We won't do)

- ❌ Cloud sync by default (optional add-on only)
- ❌ Sell or share user data
- ❌ Require internet connection for core functionality
- ❌ Lock users into proprietary formats

---

*Last Updated: 2026-03-02*
