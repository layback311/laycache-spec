//
//  LayCacheSigning.swift
//  LayCache - Device Signing Module
//
//  Created by 银月 on 2026-03-02.
//  Version: 1.0.0
//

import Foundation
import CryptoKit

// MARK: - Device Signing Manager

/// Manages device keys and bundle signing
class LayCacheSigning {

    // MARK: - Constants

    private let keychainService = "com.laycache.signing"
    private let privateKeyKey = "devicePrivateKey"
    private let publicKeyFile = "device_public_key.json"

    // MARK: - Properties

    private(set) var deviceId: String?
    private var privateKey: Ed25519.PrivateKey?

    // MARK: - Singleton

    static let shared = LayCacheSigning()

    private init() {
        loadOrGenerateKeys()
    }

    // MARK: - Key Management

    /// Load existing keys or generate new ones
    private func loadOrGenerateKeys() {
        // Try to load existing private key
        if let privateKeyData = loadPrivateKeyFromKeychain() {
            do {
                privateKey = try Ed25519.PrivateKey(rawRepresentation: privateKeyData)
                deviceId = deriveDeviceId(from: privateKey!.publicKey)
                print("✅ Loaded existing device keys: \(deviceId ?? "unknown")")
            } catch {
                print("⚠️ Failed to load private key, generating new ones")
                generateAndStoreKeys()
            }
        } else {
            // Generate new keys
            generateAndStoreKeys()
        }
    }

    /// Generate new Ed25519 key pair and store
    private func generateAndStoreKeys() {
        // Generate key pair
        privateKey = Ed25519.PrivateKey()

        // Store private key in Keychain
        let privateKeyData = privateKey!.rawRepresentation
        let success = saveToKeychain(
            data: privateKeyData,
            service: keychainService,
            key: privateKeyKey
        )

        if success {
            deviceId = deriveDeviceId(from: privateKey!.publicKey)
            print("✅ Generated new device keys: \(deviceId ?? "unknown")")

            // Export public key for sharing
            exportPublicKey()
        } else {
            print("❌ Failed to store private key in Keychain")
        }
    }

    /// Derive device ID from public key
    private func deriveDeviceId(from publicKey: Ed25519.PublicKey) -> String {
        let pubKeyData = publicKey.rawRepresentation
        let hash = SHA256.hash(data: pubKeyData)
        let prefix = hash.prefix(4).map { String(format: "%02x", $0) }.joined()
        return "dev_\(prefix)"
    }

    // MARK: - Signing

    /// Sign a manifest dictionary
    /// - Parameter manifest: The manifest to sign
    /// - Returns: Signature data (64 bytes) or nil if signing failed
    func signManifest(_ manifest: [String: Any]) -> Data? {
        guard let privateKey = privateKey else {
            print("❌ No private key available")
            return nil
        }

        // Canonicalize manifest
        guard let canonicalData = canonicalizeManifest(manifest) else {
            print("❌ Failed to canonicalize manifest")
            return nil
        }

        // Sign
        do {
            let signature = try privateKey.signature(for: canonicalData)
            return signature.rawRepresentation
        } catch {
            print("❌ Failed to sign manifest: \(error)")
            return nil
        }
    }

    /// Canonicalize manifest for signing
    /// - Parameter manifest: The manifest dictionary
    /// - Returns: Canonical JSON data
    private func canonicalizeManifest(_ manifest: [String: Any]) -> Data? {
        do {
            // Sort keys and remove whitespace
            let data = try JSONSerialization.data(
                withJSONObject: manifest,
                options: [.sortedKeys, .withoutEscapingSlashes]
            )
            return data
        } catch {
            print("❌ Failed to canonicalize: \(error)")
            return nil
        }
    }

    // MARK: - Verification

    /// Verify a signature against a manifest
    /// - Parameters:
    ///   - manifest: The manifest to verify
    ///   - signature: The signature data
    ///   - publicKeyData: The public key data
    /// - Returns: True if signature is valid
    static func verifyManifest(
        _ manifest: [String: Any],
        signature: Data,
        publicKeyData: Data
    ) -> Bool {
        do {
            // Load public key
            let publicKey = try Ed25519.PublicKey(rawRepresentation: publicKeyData)

            // Canonicalize manifest
            guard let canonicalData = try? JSONSerialization.data(
                withJSONObject: manifest,
                options: [.sortedKeys, .withoutEscapingSlashes]
            ) else {
                return false
            }

            // Verify signature
            let ed25519Signature = try Ed25519.Signature(rawRepresentation: signature)
            return publicKey.isValidSignature(ed25519Signature, for: canonicalData)
        } catch {
            print("❌ Verification failed: \(error)")
            return false
        }
    }

    // MARK: - Export/Import

    /// Export public key for sharing
    func exportPublicKey() -> URL? {
        guard let publicKey = privateKey?.publicKey else {
            return nil
        }

        let pubKeyData = publicKey.rawRepresentation
        let pubKeyBase64 = pubKeyData.base64EncodedString()

        let info: [String: Any] = [
            "deviceId": deviceId ?? "unknown",
            "publicKey": pubKeyBase64,
            "algorithm": "Ed25519",
            "createdAt": ISO8601DateFormatter().string(from: Date())
        ]

        guard let jsonData = try? JSONSerialization.data(
            withJSONObject: info,
            options: [.sortedKeys, .prettyPrinted]
        ) else {
            return nil
        }

        let fileURL = getDocumentsDirectory()
            .appendingPathComponent(publicKeyFile)

        do {
            try jsonData.write(to: fileURL)
            print("✅ Exported public key to: \(fileURL.path)")
            return fileURL
        } catch {
            print("❌ Failed to export public key: \(error)")
            return nil
        }
    }

    /// Get public key data
    func getPublicKeyData() -> Data? {
        return privateKey?.publicKey.rawRepresentation
    }

    // MARK: - Keychain Helpers

    private func saveToKeychain(data: Data, service: String, key: String) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlocked
        ]

        // Delete existing item first
        SecItemDelete(query as CFDictionary)

        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }

    private func loadPrivateKeyFromKeychain() -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: privateKeyKey,
            kSecReturnData as String: true
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        if status == errSecSuccess {
            return result as? Data
        }
        return nil
    }

    // MARK: - Helpers

    private func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}

// MARK: - Device Info

struct DeviceInfo: Codable {
    let deviceId: String
    let publicKey: String
    let algorithm: String
    let createdAt: String
    let name: String?

    init(deviceId: String, publicKey: String, name: String? = nil) {
        self.deviceId = deviceId
        self.publicKey = publicKey
        self.algorithm = "Ed25519"
        self.createdAt = ISO8601DateFormatter().string(from: Date())
        self.name = name
    }
}

// MARK: - Usage Examples

/*
 // Example 1: Sign a manifest
 let manifest: [String: Any] = [
     "version": "1.0.0",
     "exportTime": ISO8601DateFormatter().string(from: Date()),
     "deviceId": LayCacheSigning.shared.deviceId ?? "",
     "stats": ["events": 100]
 ]

 if let signature = LayCacheSigning.shared.signManifest(manifest) {
     try signature.write(to: bundleURL.appendingPathComponent("signature.bin"))
 }

 // Example 2: Verify a signature
 let publicKeyData = Data(base64Encoded: "abc123...")!
 let isValid = LayCacheSigning.verifyManifest(
     manifest,
     signature: signatureData,
     publicKeyData: publicKeyData
 )

 // Example 3: Export public key
 if let url = LayCacheSigning.shared.exportPublicKey() {
     print("Public key exported to: \(url.path)")
 }
 */
