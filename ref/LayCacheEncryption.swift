//
//  LayCacheEncryption.swift
//  LayCache V4 - Encryption Module
//
//  Created by 银月 on 2026-03-02.
//  Version: 1.0.0
//

import Foundation
import CryptoKit

// MARK: - Principal

struct Principal: Identifiable, Codable {
    let principalId: String
    let deviceId: String
    let authMethod: AuthMethod
    let createdAt: Date
    var lastAuthenticated: Date?
    
    var id: String { principalId }
    
    init(deviceId: String, authMethod: AuthMethod = .biometric) {
        self.principalId = "principal_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        self.deviceId = deviceId
        self.authMethod = authMethod
        self.createdAt = Date()
        self.lastAuthenticated = nil
    }
}

enum AuthMethod: String, Codable {
    case biometric = "biometric"
    case passcode = "passcode"
    case none = "none"
}

// MARK: - Encrypted Data

struct EncryptedData: Codable {
    let encrypted: Bool
    let algorithm: String
    let iv: String  // Base64
    let ciphertext: String  // Base64
    let tag: String  // Base64
    let keyId: String
    
    init(iv: Data, ciphertext: Data, tag: Data, keyId: String) {
        self.encrypted = true
        self.algorithm = "AES-256-GCM"
        self.iv = iv.base64EncodedString()
        self.ciphertext = ciphertext.base64EncodedString()
        self.tag = tag.base64EncodedString()
        self.keyId = keyId
    }
}

// MARK: - Encryption Provider Protocol

protocol EncryptionProvider {
    func encrypt(data: Data, keyId: String) throws -> EncryptedData
    func decrypt(encrypted: EncryptedData, keyId: String) throws -> Data
    func generateKey() throws -> String
}

// MARK: - AES-GCM Encryption Provider

class AESGCMEncryptionProvider: EncryptionProvider {
    
    private var keys: [String: SymmetricKey] = [:]
    
    // MARK: - Key Management
    
    func generateKey() throws -> String {
        let key = SymmetricKey(size: .bits256)
        let keyId = "key_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        keys[keyId] = key
        return keyId
    }
    
    func generateKey(from masterKey: Data, salt: Data) throws -> String {
        // HKDF key derivation
        let inputKeyMaterial = SymmetricKey(data: masterKey)
        let derivedKey = HKDF<SHA256>.deriveKey(
            inputKeyMaterial: inputKeyMaterial,
            salt: salt,
            info: Data("laycache-block-encryption".utf8),
            outputByteCount: 32
        )
        
        let keyId = "key_\(salt.base64EncodedString().prefix(16))"
        keys[keyId] = derivedKey
        return keyId
    }
    
    // MARK: - Encryption
    
    func encrypt(data: Data, keyId: String) throws -> EncryptedData {
        guard let key = keys[keyId] else {
            throw EncryptionError.keyNotFound(keyId)
        }
        
        // Generate random IV
        let iv = AES.GCM.Nonce()
        
        // Encrypt
        let sealedBox = try AES.GCM.seal(data, using: key, nonce: iv)
        
        return EncryptedData(
            iv: iv.withUnsafeBytes { Data($0) },
            ciphertext: sealedBox.ciphertext,
            tag: sealedBox.tag,
            keyId: keyId
        )
    }
    
    // MARK: - Decryption
    
    func decrypt(encrypted: EncryptedData, keyId: String) throws -> Data {
        guard let key = keys[keyId] else {
            throw EncryptionError.keyNotFound(keyId)
        }
        
        guard let iv = Data(base64Encoded: encrypted.iv),
              let ciphertext = Data(base64Encoded: encrypted.ciphertext),
              let tag = Data(base64Encoded: encrypted.tag) else {
            throw EncryptionError.invalidData
        }
        
        // Reconstruct sealed box
        let nonce = try AES.GCM.Nonce(data: iv)
        let sealedBox = try AES.GCM.SealedBox(
            nonce: nonce,
            ciphertext: ciphertext,
            tag: tag
        )
        
        // Decrypt
        return try AES.GCM.open(sealedBox, using: key)
    }
    
    // MARK: - Key Backup
    
    func backupKey(keyId: String, password: String) throws -> Data {
        guard let key = keys[keyId] else {
            throw EncryptionError.keyNotFound(keyId)
        }
        
        // Derive encryption key from password
        let salt = Data(UUID().uuidString.utf8)
        let passwordKey = try deriveKeyFromPassword(password, salt: salt, iterations: 100000)
        
        // Encrypt the key
        let keyData = key.withUnsafeBytes { Data($0) }
        let encrypted = try AES.GCM.seal(keyData, using: passwordKey)
        
        // Package: salt + nonce + ciphertext + tag
        var backup = salt
        backup.append(encrypted.nonce.withUnsafeBytes { Data($0) })
        backup.append(encrypted.ciphertext)
        backup.append(encrypted.tag)
        
        return backup
    }
    
    func restoreKey(from backup: Data, password: String) throws -> String {
        // Extract components
        guard backup.count >= 16 + 12 + 16 + 16 else {
            throw EncryptionError.invalidData
        }
        
        let salt = backup.prefix(16)
        let nonceData = backup.dropFirst(16).prefix(12)
        let ciphertext = backup.dropFirst(28).dropLast(16)
        let tag = backup.suffix(16)
        
        // Derive key from password
        let passwordKey = try deriveKeyFromPassword(password, salt: salt, iterations: 100000)
        
        // Decrypt
        let nonce = try AES.GCM.Nonce(data: nonceData)
        let sealedBox = try AES.GCM.SealedBox(
            nonce: nonce,
            ciphertext: ciphertext,
            tag: tag
        )
        
        let keyData = try AES.GCM.open(sealedBox, using: passwordKey)
        let key = SymmetricKey(data: keyData)
        
        let keyId = "key_restored_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        keys[keyId] = key
        
        return keyId
    }
    
    // MARK: - Helpers
    
    private func deriveKeyFromPassword(_ password: String, salt: Data, iterations: Int) throws -> SymmetricKey {
        guard let passwordData = password.data(using: .utf8) else {
            throw EncryptionError.invalidPassword
        }
        
        // PBKDF2
        let derivedKey = try PBKDF2.deriveKey(
            password: passwordData,
            salt: salt,
            iterations: iterations,
            keyLength: 32
        )
        
        return SymmetricKey(data: derivedKey)
    }
}

// MARK: - PBKDF2 Helper

enum PBKDF2 {
    static func deriveKey(password: Data, salt: Data, iterations: Int, keyLength: Int) throws -> Data {
        var derivedKey = Data(count: keyLength)
        
        let result = derivedKey.withUnsafeMutableBytes { derivedKeyBytes in
            password.withUnsafeBytes { passwordBytes in
                salt.withUnsafeBytes { saltBytes in
                    CCKeyDerivationPBKDF(
                        CCPBKDFAlgorithm(kCCPBKDF2),
                        passwordBytes.baseAddress?.assumingMemoryBound(to: Int8.self),
                        password.count,
                        saltBytes.baseAddress?.assumingMemoryBound(to: UInt8.self),
                        salt.count,
                        CCPseudoRandomAlgorithm(kCCPRFHmacAlgSHA256),
                        UInt32(iterations),
                        derivedKeyBytes.baseAddress?.assumingMemoryBound(to: UInt8.self),
                        keyLength
                    )
                }
            }
        }
        
        guard result == kCCSuccess else {
            throw EncryptionError.keyDerivationFailed
        }
        
        return derivedKey
    }
}

// CommonCrypto import
import CommonCrypto

// MARK: - Errors

enum EncryptionError: Error, LocalizedError {
    case keyNotFound(String)
    case invalidData
    case invalidPassword
    case keyDerivationFailed
    case encryptionFailed
    case decryptionFailed
    
    var errorDescription: String? {
        switch self {
        case .keyNotFound(let id):
            return "Key not found: \(id)"
        case .invalidData:
            return "Invalid encrypted data"
        case .invalidPassword:
            return "Invalid password"
        case .keyDerivationFailed:
            return "Key derivation failed"
        case .encryptionFailed:
            return "Encryption failed"
        case .decryptionFailed:
            return "Decryption failed"
        }
    }
}

// MARK: - Usage Examples

/*
 // 创建加密提供者
 let provider = AESGCMEncryptionProvider()
 
 // 生成密钥
 let keyId = try provider.generateKey()
 
 // 加密数据
 let originalData = "敏感数据".data(using: .utf8)!
 let encrypted = try provider.encrypt(data: originalData, keyId: keyId)
 
 // 解密数据
 let decrypted = try provider.decrypt(encrypted: encrypted, keyId: keyId)
 
 // 备份密钥（用密码加密）
 let backup = try provider.backupKey(keyId: keyId, password: "my_password")
 
 // 恢复密钥
 let restoredKeyId = try provider.restoreKey(from: backup, password: "my_password")
 */
