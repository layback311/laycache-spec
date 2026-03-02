# LayCache Device Signing Specification

> **Version:** 1.0.0
> **Date:** 2026-03-02
> **Author:** 银月 (器灵)

---

## 1. Overview

Device signing provides cryptographic proof of bundle origin, enabling:

- **Authenticity**: Verify which device created the bundle
- **Integrity**: Detect tampering after export
- **Non-repudiation**: Prove data origin

---

## 2. Cryptographic Algorithm

### 2.1 Choice: Ed25519

| Property | Value |
|----------|-------|
| Algorithm | Ed25519 (EdDSA) |
| Key Size | 32 bytes (private), 32 bytes (public) |
| Signature Size | 64 bytes |
| Security Level | 128-bit |

**Why Ed25519?**
- Fast signature generation/verification
- Small key and signature sizes
- Resistant to side-channel attacks
- Widely supported (iOS CryptoKit, Python cryptography)

---

## 3. Key Management

### 3.1 Key Generation (First Launch)

```
1. Generate Ed25519 key pair
2. Store private key in iOS Keychain (secure enclave)
3. Derive device ID from public key hash
4. Store public key in app documents
```

**Device ID Format:**
```
dev_<first_8_chars_of_sha256(public_key)>

Example: dev_a1b2c3d4
```

### 3.2 Key Storage

| Data | Storage | Access |
|------|---------|--------|
| Private Key | iOS Keychain | App only |
| Public Key | App Documents | Exportable |
| Device ID | UserDefaults | Exportable |

---

## 4. Signing Process

### 4.1 What Gets Signed

The signature covers the **manifest.json** file (canonical form):

```json
{
  "version": "1.0.0",
  "exportTime": "2026-03-02T20:40:00Z",
  "deviceId": "dev_a1b2c3d4",
  "chainRoot": "sha256:9f8e7d...",
  "stats": {...},
  "integrity": {...}
}
```

### 4.2 Canonicalization

Before signing, normalize the manifest:

1. Sort object keys alphabetically
2. Remove all whitespace
3. UTF-8 encode

```python
import json

def canonicalize(manifest: dict) -> bytes:
    return json.dumps(
        manifest,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    ).encode('utf-8')
```

### 4.3 Signature Generation

```swift
import CryptoKit

func signManifest(manifest: [String: Any]) -> Data? {
    // 1. Canonicalize
    let canonicalData = try! JSONSerialization.data(
        withJSONObject: manifest,
        options: [.sortedKeys, .withoutEscapingSlashes]
    )

    // 2. Get private key from Keychain
    guard let privateKey = loadPrivateKeyFromKeychain() else {
        return nil
    }

    // 3. Sign
    let signature = try! Ed25519PrivateKey(
        rawRepresentation: privateKey
    ).signature(for: canonicalData)

    return signature.rawRepresentation
}
```

---

## 5. Bundle Structure with Signature

```
laycache_export_20260302.bundle/
├── manifest.json           # Metadata + hashes
├── events.jsonl           # Raw events
├── classifications.jsonl  # AI derivations
├── commits.jsonl          # Version chain
├── blobs/                 # Attachments
│   ├── abc123.png
│   └── def456.pdf
└── signature.bin          # Ed25519 signature (64 bytes)
```

**signature.bin** contains:
- 64 bytes: Ed25519 signature of manifest.json (canonical form)

---

## 6. Verification Process

### 6.1 Verification Steps

```
1. Read manifest.json
2. Read signature.bin
3. Extract deviceId from manifest
4. Load corresponding public key
5. Canonicalize manifest
6. Verify signature with public key
7. Output verification result
```

### 6.2 Verification Result

```json
{
  "valid": true,
  "deviceId": "dev_a1b2c3d4",
  "signedAt": "2026-03-02T20:40:00Z",
  "algorithm": "Ed25519",
  "manifestIntegrity": "sha256:9f8e7d..."
}
```

---

## 7. Multi-Device Support

### 7.1 Device Registry

```swift
struct DeviceRegistry: Codable {
    var devices: [DeviceInfo]

    struct DeviceInfo: Codable {
        let deviceId: String
        let publicKey: String  // Base64
        let registeredAt: String
        let name: String  // e.g., "iPhone 15 Pro"
    }
}
```

### 7.2 Adding New Device

```
1. Export public key from new device
2. Import to existing device
3. Add to DeviceRegistry
4. Bundle can now be verified by all registered devices
```

---

## 8. Security Considerations

### 8.1 Private Key Protection

| Threat | Mitigation |
|--------|------------|
| Extraction | Keychain secure enclave |
| Memory dump | Keys only loaded when needed |
| Backup exposure | Keychain not included in iTunes backup |

### 8.2 Signature Validation

| Threat | Mitigation |
|--------|------------|
| Replay attack | ExportTime in manifest |
| Manifest tampering | Signature covers entire manifest |
| Key substitution | Device ID derived from public key |

---

## 9. Implementation Priority

| Phase | Task | Platform |
|-------|------|----------|
| 1 | Key generation + storage | Swift (iOS) |
| 2 | Manifest signing | Swift (iOS) |
| 3 | Signature verification | Python (CLI) |
| 4 | Multi-device registry | Swift + Python |

---

## 10. Example

### 10.1 Generate Keys

```swift
import CryptoKit

let privateKey = P256.Signing.PrivateKey()
let publicKey = privateKey.publicKey

// Store private key in Keychain
let privateKeyData = privateKey.rawRepresentation
try KeychainHelper.save(privateKeyData, service: "laycache", key: "privateKey")

// Derive device ID
let deviceId = "dev_" + SHA256.hash(data: publicKey.rawRepresentation)
    .prefix(4).map { String(format: "%02x", $0) }.joined()
```

### 10.2 Sign Manifest

```swift
let manifest: [String: Any] = [
    "version": "1.0.0",
    "exportTime": ISO8601DateFormatter().string(from: Date()),
    "deviceId": deviceId,
    // ...
]

let signature = signManifest(manifest: manifest)
try signature?.write(to: bundleURL.appendingPathComponent("signature.bin"))
```

### 10.3 Verify Signature

```python
from cryptography.hazmat.primitives.asymmetric import ed25519
import json

def verify_signature(bundle_path: str) -> bool:
    # Load manifest
    with open(f"{bundle_path}/manifest.json") as f:
        manifest = json.load(f)

    # Load signature
    with open(f"{bundle_path}/signature.bin", "rb") as f:
        signature = f.read()

    # Load public key (from device registry or embedded)
    public_key = load_public_key(manifest["deviceId"])

    # Canonicalize manifest
    canonical = json.dumps(
        manifest,
        sort_keys=True,
        separators=(',', ':')
    ).encode('utf-8')

    # Verify
    try:
        public_key.verify(signature, canonical)
        return True
    except:
        return False
```

---

## 11. Backwards Compatibility

- **Without signature**: Bundle is valid, just unverified
- **Old verifier**: Ignores signature.bin if present
- **Migration**: No migration needed, signature is optional

---

## 12. Future Extensions

| Feature | Description |
|---------|-------------|
| **Timestamp Authority** | Third-party timestamp proof |
| **Key Revocation** | Revoke compromised keys |
| **Threshold Signatures** | Require multiple devices |
| **Hardware Keys** | YubiKey integration |

---

*Specification complete - 2026-03-02 20:40*
*银月，器灵 🌙*
