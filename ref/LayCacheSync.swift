//
//  LayCacheSync.swift
//  LayCache V5 - Sync Protocol
//
//  Created by 银月 on 2026-03-02.
//  Version: 1.0.0 (Alpha)
//

import Foundation

// MARK: - Version Vector

typealias VersionVector = [String: String]  // deviceId -> lastEventTimestamp

// MARK: - Sync Message

enum SyncMessage: Codable {
    case handshake(Handshake)
    case syncRequest(SyncRequest)
    case syncResponse(SyncResponse)
    
    struct Handshake: Codable {
        let protocol: String = "laycache-sync"
        let version: String = "1.0.0"
        let deviceId: String
        let versionVector: VersionVector
    }
    
    struct SyncRequest: Codable {
        let type: String = "sync_request"
        let deviceId: String
        let since: VersionVector
    }
    
    struct SyncResponse: Codable {
        let type: String = "sync_response"
        let deviceId: String
        let events: [Event]
        let newVersionVector: VersionVector
    }
}

// MARK: - Event (Simplified)

struct Event: Codable {
    let eventId: String
    let type: String
    let content: [String: JSONValue]
    let timestamp: String
    let deviceId: String
    var previousHash: String?
}

enum JSONValue: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case array([JSONValue])
    case object([String: JSONValue])
    case null
}

// MARK: - Conflict

struct Conflict: Codable {
    let conflictId: String
    let conflictingEventId: String
    let localVersion: Event
    let remoteVersion: Event
    var resolution: Resolution = .manual
    var resolvedAt: String?
    let createdAt: String
    
    enum Resolution: String, Codable {
        case manual = "manual"
        case autoEarliest = "auto_earliest"
        case autoLatest = "auto_latest"
    }
}

// MARK: - Sync Manager

class LayCacheSyncManager {
    
    private let deviceId: String
    private var versionVector: VersionVector = [:]
    private var events: [Event] = []
    private var conflicts: [Conflict] = []
    
    init(deviceId: String) {
        self.deviceId = deviceId
    }
    
    // MARK: - Version Vector
    
    func updateVersionVector(_ newVector: VersionVector) {
        for (deviceId, timestamp) in newVector {
            if let existing = versionVector[deviceId] {
                if timestamp > existing {
                    versionVector[deviceId] = timestamp
                }
            } else {
                versionVector[deviceId] = timestamp
            }
        }
    }
    
    func getVersionVector() -> VersionVector {
        return versionVector
    }
    
    // MARK: - Sync Protocol
    
    /// 创建握手消息
    func createHandshake() -> SyncMessage.Handshake {
        return SyncMessage.Handshake(
            deviceId: deviceId,
            versionVector: versionVector
        )
    }
    
    /// 创建同步请求
    func createSyncRequest(remoteVector: VersionVector) -> SyncMessage.SyncRequest {
        var since: VersionVector = [:]
        
        for (deviceId, timestamp) in remoteVector {
            if let localTimestamp = versionVector[deviceId] {
                if localTimestamp > timestamp {
                    since[deviceId] = timestamp
                }
            }
            // 如果本地没有这个设备的数据，不需要请求
        }
        
        return SyncMessage.SyncRequest(
            deviceId: self.deviceId,
            since: since
        )
    }
    
    /// 处理同步请求
    func handleSyncRequest(_ request: SyncMessage.SyncRequest) -> SyncMessage.SyncResponse {
        // 找出需要发送的events
        var eventsToSend: [Event] = []
        
        for event in events {
            if let sinceTimestamp = request.since[event.deviceId] {
                if event.timestamp > sinceTimestamp {
                    eventsToSend.append(event)
                }
            } else {
                // 远程没有这个设备的数据，发送所有
                if event.deviceId == deviceId {
                    eventsToSend.append(event)
                }
            }
        }
        
        // 按时间戳排序
        eventsToSend.sort { $0.timestamp < $1.timestamp }
        
        return SyncMessage.SyncResponse(
            deviceId: self.deviceId,
            events: eventsToSend,
            newVersionVector: versionVector
        )
    }
    
    /// 处理同步响应
    func handleSyncResponse(_ response: SyncMessage.SyncResponse) -> MergeResult {
        let result = mergeEvents(response.events)
        updateVersionVector(response.newVersionVector)
        return result
    }
    
    // MARK: - Merge Algorithm
    
    func mergeEvents(_ remoteEvents: [Event]) -> MergeResult {
        var eventsAdded = 0
        var conflictsDetected = 0
        
        for remoteEvent in remoteEvents {
            // 检查是否已存在
            if let existingIndex = events.firstIndex(where: { $0.eventId == remoteEvent.eventId }) {
                let existing = events[existingIndex]
                
                // 检查哈希是否一致
                if !hashesMatch(existing, remoteEvent) {
                    // 检测到冲突
                    let conflict = Conflict(
                        conflictId: "conflict_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))",
                        conflictingEventId: remoteEvent.eventId,
                        localVersion: existing,
                        remoteVersion: remoteEvent,
                        createdAt: ISO8601DateFormatter().string(from: Date())
                    )
                    
                    conflicts.append(conflict)
                    conflictsDetected += 1
                    
                    // 不覆盖本地，保留冲突
                }
            } else {
                // 新event，追加
                events.append(remoteEvent)
                eventsAdded += 1
                
                // 更新version vector
                versionVector[remoteEvent.deviceId] = remoteEvent.timestamp
            }
        }
        
        // 重新排序
        events.sort { $0.timestamp < $1.timestamp }
        
        // 重新计算哈希链
        recalculateHashChain()
        
        return MergeResult(
            eventsAdded: eventsAdded,
            conflictsDetected: conflictsDetected,
            conflicts: conflicts
        )
    }
    
    private func hashesMatch(_ e1: Event, _ e2: Event) -> Bool {
        // 简化版：检查关键字段是否一致
        // 实际应该计算完整的哈希
        return e1.type == e2.type &&
               e1.timestamp == e2.timestamp &&
               e1.deviceId == e2.deviceId
    }
    
    private func recalculateHashChain() {
        // 重新计算所有previousHash
        for i in 1..<events.count {
            let previous = events[i-1]
            let hash = calculateEventHash(previous)
            events[i].previousHash = hash
        }
    }
    
    private func calculateEventHash(_ event: Event) -> String {
        // 简化版：实际应该用SHA256
        return "hash_\(event.eventId)_\(event.timestamp)"
    }
    
    // MARK: - Conflict Resolution
    
    func getConflicts() -> [Conflict] {
        return conflicts.filter { $0.resolvedAt == nil }
    }
    
    func resolveConflict(conflictId: String, keepVersion: ConflictVersion) throws {
        guard let index = conflicts.firstIndex(where: { $0.conflictId == conflictId }) else {
            throw SyncError.conflictNotFound(conflictId)
        }
        
        let conflict = conflicts[index]
        
        // 根据选择更新event
        let chosenEvent = keepVersion == .local ? conflict.localVersion : conflict.remoteVersion
        
        // 找到并更新event
        if let eventIndex = events.firstIndex(where: { $0.eventId == conflict.conflictingEventId }) {
            events[eventIndex] = chosenEvent
        }
        
        // 标记冲突已解决
        conflicts[index].resolvedAt = ISO8601DateFormatter().string(from: Date())
        
        // 创建resolution event
        createResolutionEvent(conflict: conflict, chosenVersion: keepVersion)
    }
    
    private func createResolutionEvent(conflict: Conflict, chosenVersion: ConflictVersion) {
        let resolutionEvent = Event(
            eventId: "evt_resolution_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))",
            type: "conflict.resolved",
            content: [
                "conflictEventId": .string(conflict.conflictId),
                "chosenVersion": .string(chosenVersion.rawValue)
            ],
            timestamp: ISO8601DateFormatter().string(from: Date()),
            deviceId: deviceId,
            previousHash: nil
        )
        
        events.append(resolutionEvent)
    }
}

// MARK: - Supporting Types

struct MergeResult {
    let eventsAdded: Int
    let conflictsDetected: Int
    let conflicts: [Conflict]
}

enum ConflictVersion: String {
    case local = "local"
    case remote = "remote"
}

enum SyncError: Error, LocalizedError {
    case conflictNotFound(String)
    case invalidMessage
    case syncFailed(String)
    
    var errorDescription: String? {
        switch self {
        case .conflictNotFound(let id):
            return "Conflict not found: \(id)"
        case .invalidMessage:
            return "Invalid sync message"
        case .syncFailed(let reason):
            return "Sync failed: \(reason)"
        }
    }
}

// MARK: - Usage Examples

/*
 // 创建同步管理器
 let sync = LayCacheSyncManager(deviceId: "dev_abc123")
 
 // 创建握手
 let handshake = sync.createHandshake()
 
 // 创建同步请求
 let request = sync.createSyncRequest(remoteVector: ["dev_xyz789": "2026-03-02T21:00:00Z"])
 
 // 处理同步响应
 let result = sync.handleSyncResponse(response)
 print("Added \(result.eventsAdded) events")
 print("Conflicts: \(result.conflictsDetected)")
 
 // 解决冲突
 let conflicts = sync.getConflicts()
 for conflict in conflicts {
     try sync.resolveConflict(conflictId: conflict.conflictId, keepVersion: .local)
 }
 */
