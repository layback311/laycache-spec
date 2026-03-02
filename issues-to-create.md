# GitHub Issues to Create

## 1. Define Event Schema (v1)
**Title:** Define minimum objects: Event / Derivation / Commit

**Description:**
Design the core data structures:
- **Event**: Raw capture (text, image, audio)
- **Derivation**: AI-generated summary/classification
- **Commit**: Snapshot of state at a point in time

**Fields to define:**
- `id`: UUID v4
- `timestamp`: ISO 8601
- `type`: "event" | "derivation" | "commit"
- `content`: Payload (encrypted)
- `hash`: SHA-256 of content
- `prev_hash`: Hash of previous block (for chain)

**Acceptance Criteria:**
- [ ] JSON Schema draft committed
- [ ] Fields documented in spec/event.md
- [ ] Example JSON objects provided

---

## 2. Define Derivation Input Hash Semantics
**Title:** Define hash reference rules for derivation.inputs

**Description:**
When a Derivation references input Events, how should we compute the verify the hash?

**Options:**
1. Hash the concatenation of input event IDs
2. Store array of input hashes
3. Merkle tree approach

**Acceptance Criteria:**
- [ ] Chash method documented
- [ ] Collision resistance considered
- [ ] Performance benchmarked

---

## 3. Define Rollback Semantics
**Title:** Choose rollback implementation approach

**Description:**
How should "undo" work?

**Options:**
1. **revert commit** - Create new commit that undoes changes
2. **checkout-to-commit** - Restore state to a historical commit
3. **branch** - Create alternate timeline

**Acceptance Criteria:**
- [ ] Rollback method documented
- [ ] Example scenarios provided
- [ ] Data loss scenarios handled

---

## 4. Define Export Bundle v0
**Title:** Design export/import bundle format

**Description:**
How should users export their data?

**Structure:**
```
bundle_v0/
├── manifest.json     # Metadata
├── events/           # Event JSON files
├── derivations/      # Derivation JSON files
├── commits/         # Commit JSON files
└── attachments/     # Binary files (images, etc.)
```

**Acceptance Criteria:**
- [ ] Format documented in spec/export-bundle-v0.md
- [ ] Export implementation working
- [ ] Import implementation working
- [ ] Sample bundle provided

---

## 5. Define External Audit Object
**Title:** Design audit trail for external AI services

**Description:**
When sending data to external AI services (e.g., OpenAI, Anthropic), what should we log?

**Fields to log:**
- `timestamp`: When the call was made
- `service`: Which service (e.g., "openai", "anthropic")
- `model`: Which model (e.g., "gpt-4", "claude-3")
- `request_hash`: Hash of request (for verification)
- `response_hash`: Hash of response
- `tokens_in` / `tokens_out`: Token usage
- `latency_ms`: Response time
- `success`: Whether call succeeded
- `error_message`: If failed, what went wrong

**Redaction Rules:**
- ❌ Never log full request/response content
- ✅ Only log metadata and hashes
- ✅ Token counts are OK
- ✅ Timing is OK

**Acceptance Criteria:**
- [ ] Schema defined in spec/audit-v0.md
- [ ] Privacy-safe examples provided
- [ ] Redaction rules documented

---

## 6. Create JSON Schema v0
**Title:** Write JSON Schema for all core objects

**Description:**
Create formal JSON Schema for:
- Event
- Derivation
- Commit
- AuditEntry

**Acceptance Criteria:**
- [ ] schemas/event-v0.json
- [ ] schemas/derivation-v0.json
- [ ] schemas/commit-v0.json
- [ ] schemas/audit-v0.json
- [ ] Validation tests passing

---

## 7. Create Privacy-Safe Example Dataset
**Title:** Generate example data for testing

**Description:**
Create a set of example Events, Derivations, and Commits that contain **no real user data**.

**Examples:**
- "Meeting at 3pm"
- "Buy groceries: milk, eggs, bread"
- "Remember to call mom"

**Acceptance Criteria:**
- [ ] examples/events.json with 10+ examples
- [ ] examples/derivations.json with 5+ examples
- [ ] examples/commits.json with 3+ examples
- [ ] No personal information included
- [ ] Examples are realistic and diverse

---

## 8. Write ADR Template + First ADR
**Title:** Document architecture decisions

**Description:**
Create an Architecture Decision Record (ADR) template and write the first ADR.

**ADR Template:**
```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue that we're addressing?]

## Decision
[What is the change that we're proposing/making?]

## Consequences
[What are the positive and negative outcomes?]

## Alternatives Considered
[What other options did we consider?]
```

**First ADR:**
"ADR-001: Why iOS/Swift as v1 Reference Implementation"
- Rationale: Native performance, LocalAuthentication support, offline-first
- Alternatives: React Native, Flutter. PWA.

**Acceptance Criteria:**
- [ ] decisions/adr-template.md created
- [ ] decisions/adr-001.md created
- [ ] Template documented
