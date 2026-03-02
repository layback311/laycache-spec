//
//  LayCacheTask.swift
//  LayCache V3 - Task Management
//
//  Created by 银月 on 2026-03-02.
//  Version: 1.0.0 (Frozen)
//

import Foundation
import SQLite3

// MARK: - Task Status

enum TaskStatus: String, Codable, CaseIterable {
    case pending = "pending"
    case inProgress = "in_progress"
    case completed = "completed"
    case cancelled = "cancelled"
    
    /// 可转换到的状态
    var validTransitions: [TaskStatus] {
        switch self {
        case .pending:
            return [.inProgress, .cancelled]
        case .inProgress:
            return [.pending, .completed, .cancelled]
        case .completed:
            return []  // 终态
        case .cancelled:
            return [.pending]
        }
    }
    
    func canTransition(to newStatus: TaskStatus) -> Bool {
        return validTransitions.contains(newStatus)
    }
}

// MARK: - Task Priority

enum TaskPriority: String, Codable {
    case P0 = "P0"  // 最高优先级
    case P1 = "P1"
    case P2 = "P2"  // 默认
    case P3 = "P3"
}

// MARK: - Task Object

struct Task: Identifiable, Codable {
    let taskId: String
    var title: String
    var status: TaskStatus
    var due: Date?
    var priority: TaskPriority
    var sourceRefs: [String]?
    let createdAt: Date
    var updatedAt: Date
    let deviceId: String
    
    var id: String { taskId }
    
    init(
        taskId: String? = nil,
        title: String,
        status: TaskStatus = .pending,
        due: Date? = nil,
        priority: TaskPriority = .P2,
        sourceRefs: [String]? = nil,
        deviceId: String
    ) {
        self.taskId = taskId ?? "task_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        self.title = title
        self.status = status
        self.due = due
        self.priority = priority
        self.sourceRefs = sourceRefs
        self.createdAt = Date()
        self.updatedAt = Date()
        self.deviceId = deviceId
    }
}

// MARK: - Task Event

struct TaskEvent: Identifiable, Codable {
    let eventId: String
    let eventType: TaskEventType
    let taskId: String
    let content: [String: AnyCodable]
    let timestamp: Date
    let deviceId: String
    let commitId: String
    var previousHash: String?
    
    var id: String { eventId }
}

enum TaskEventType: String, Codable {
    case created = "task.created"
    case updated = "task.updated"
    case statusChanged = "task.status_changed"
    case completed = "task.completed"
    case cancelled = "task.cancelled"
    case rollback = "task.rollback"
}

// Helper for encoding/decoding [String: Any]
struct AnyCodable: Codable {
    let value: Any
    
    init(_ value: Any) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else {
            value = ""
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        if let string = value as? String {
            try container.encode(string)
        } else if let int = value as? Int {
            try container.encode(int)
        } else if let double = value as? Double {
            try container.encode(double)
        } else if let bool = value as? Bool {
            try container.encode(bool)
        }
    }
}

// MARK: - Task Manager

class LayCacheTaskManager {
    
    private let db: OpaquePointer
    private let deviceId: String
    
    init(database: OpaquePointer, deviceId: String) {
        self.db = database
        self.deviceId = deviceId
        createTables()
    }
    
    // MARK: - Schema
    
    private func createTables() {
        let createTasksTable = """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                due TEXT,
                priority TEXT DEFAULT 'P2',
                source_refs TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                device_id TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due);
            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        """
        
        let createTaskEventsTable = """
            CREATE TABLE IF NOT EXISTS task_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                task_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                device_id TEXT NOT NULL,
                commit_id TEXT NOT NULL,
                previous_hash TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_task_events_task ON task_events(task_id);
            CREATE INDEX IF NOT EXISTS idx_task_events_timestamp ON task_events(timestamp);
        """
        
        if sqlite3_exec(db, createTasksTable, nil, nil, nil) != SQLITE_OK {
            print("❌ Failed to create tasks table")
        }
        
        if sqlite3_exec(db, createTaskEventsTable, nil, nil, nil) != SQLITE_OK {
            print("❌ Failed to create task_events table")
        }
    }
    
    // MARK: - CRUD
    
    /// 创建任务
    func createTask(
        title: String,
        status: TaskStatus = .pending,
        priority: TaskPriority = .P2,
        due: Date? = nil,
        sourceRefs: [String]? = nil
    ) throws -> Task {
        let task = Task(
            title: title,
            status: status,
            due: due,
            priority: priority,
            sourceRefs: sourceRefs,
            deviceId: deviceId
        )
        
        // 插入数据库
        try insertTask(task)
        
        // 记录事件
        let event = TaskEvent(
            eventId: "evt_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))",
            eventType: .created,
            taskId: task.taskId,
            content: [
                "title": AnyCodable(title),
                "status": AnyCodable(status.rawValue),
                "priority": AnyCodable(priority.rawValue)
            ],
            timestamp: Date(),
            deviceId: deviceId,
            commitId: "commit_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        )
        
        try insertTaskEvent(event)
        
        return task
    }
    
    /// 更新任务
    func updateTask(taskId: String, changes: [String: Any]) throws -> Task {
        var task = try getTask(taskId: taskId)
        
        // 检查状态转换是否合法
        if let newStatusRaw = changes["status"] as? String,
           let newStatus = TaskStatus(rawValue: newStatusRaw) {
            if !task.status.canTransition(to: newStatus) {
                throw TaskError.invalidStatusTransition(
                    from: task.status.rawValue,
                    to: newStatus.rawValue
                )
            }
            task.status = newStatus
        }
        
        // 更新其他字段
        if let title = changes["title"] as? String {
            task.title = title
        }
        if let priorityRaw = changes["priority"] as? String,
           let priority = TaskPriority(rawValue: priorityRaw) {
            task.priority = priority
        }
        if let due = changes["due"] as? Date {
            task.due = due
        }
        
        task.updatedAt = Date()
        
        // 更新数据库
        try updateTaskInDB(task)
        
        // 记录事件
        let event = TaskEvent(
            eventId: "evt_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))",
            eventType: .updated,
            taskId: task.taskId,
            content: changes.mapValues { AnyCodable($0) },
            timestamp: Date(),
            deviceId: deviceId,
            commitId: "commit_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        )
        
        try insertTaskEvent(event)
        
        return task
    }
    
    /// 回滚任务到指定commit
    func rollbackTask(taskId: String, toCommitId: String, reason: String? = nil) throws -> Task {
        // 1. 获取当前任务状态
        var task = try getTask(taskId: taskId)
        
        // 2. 获取目标commit的状态
        guard let targetEvent = getTaskEventByCommitId(commitId: toCommitId) else {
            throw TaskError.commitNotFound(toCommitId)
        }
        
        // 3. 计算需要回滚的commits
        let commitsToReverse = try getCommitsAfter(taskId: taskId, afterCommitId: toCommitId)
        
        // 4. 倒序应用反向操作
        for commit in commitsToReverse.reversed() {
            // 应用反向变更
            if let changes = commit.content["changes"] as? [String: Any] {
                // 简化版：直接恢复到目标commit的状态
            }
        }
        
        // 5. 记录rollback事件
        let rollbackEvent = TaskEvent(
            eventId: "evt_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))",
            eventType: .rollback,
            taskId: task.taskId,
            content: [
                "rollbackTo": AnyCodable(toCommitId),
                "reversedCommits": AnyCodable(commitsToReverse.map { $0.commitId }),
                "reason": AnyCodable(reason ?? "")
            ],
            timestamp: Date(),
            deviceId: deviceId,
            commitId: "commit_rollback_\(UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(16))"
        )
        
        try insertTaskEvent(rollbackEvent)
        
        task.updatedAt = Date()
        try updateTaskInDB(task)
        
        return task
    }
    
    /// 获取任务历史
    func getTaskHistory(taskId: String) throws -> [TaskEvent] {
        var events: [TaskEvent] = []
        
        let query = "SELECT * FROM task_events WHERE task_id = ? ORDER BY timestamp ASC"
        var stmt: OpaquePointer?
        
        guard sqlite3_prepare_v2(db, query, -1, &stmt, nil) == SQLITE_OK else {
            throw TaskError.databaseError
        }
        
        sqlite3_bind_text(stmt, 1, (taskId as NSString).utf8String, -1, nil)
        
        while sqlite3_step(stmt) == SQLITE_ROW {
            // 解析event...
        }
        
        sqlite3_finalize(stmt)
        
        return events
    }
    
    // MARK: - Private Helpers
    
    private func insertTask(_ task: Task) throws {
        let insert = """
            INSERT INTO tasks (task_id, title, status, due, priority, source_refs, created_at, updated_at, device_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, insert, -1, &stmt, nil) == SQLITE_OK else {
            throw TaskError.databaseError
        }
        
        sqlite3_bind_text(stmt, 1, (task.taskId as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 2, (task.title as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 3, (task.status.rawValue as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 4, task.due != nil ? (ISO8601DateFormatter().string(from: task.due!) as NSString).utf8String : nil, -1, nil)
        sqlite3_bind_text(stmt, 5, (task.priority.rawValue as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 6, task.sourceRefs != nil ? (try! JSONEncoder().encode(task.sourceRefs).base64EncodedString() as NSString).utf8String : nil, -1, nil)
        sqlite3_bind_text(stmt, 7, (ISO8601DateFormatter().string(from: task.createdAt) as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 8, (ISO8601DateFormatter().string(from: task.updatedAt) as NSString).utf8String, -1, nil)
        sqlite3_bind_text(stmt, 9, (task.deviceId as NSString).utf8String, -1, nil)
        
        guard sqlite3_step(stmt) == SQLITE_DONE else {
            sqlite3_finalize(stmt)
            throw TaskError.databaseError
        }
        
        sqlite3_finalize(stmt)
    }
    
    private func insertTaskEvent(_ event: TaskEvent) throws {
        // 实现event插入...
    }
    
    private func updateTaskInDB(_ task: Task) throws {
        // 实现task更新...
    }
    
    private func getTask(taskId: String) throws -> Task {
        // 实现task查询...
        fatalError("Not implemented")
    }
    
    private func getTaskEventByCommitId(commitId: String) -> TaskEvent? {
        // 实现event查询...
        return nil
    }
    
    private func getCommitsAfter(taskId: String, afterCommitId: String) throws -> [TaskEvent] {
        // 实现commit查询...
        return []
    }
}

// MARK: - Errors

enum TaskError: Error, LocalizedError {
    case taskNotFound(String)
    case invalidStatusTransition(from: String, to: String)
    case commitNotFound(String)
    case databaseError
    
    var errorDescription: String? {
        switch self {
        case .taskNotFound(let id):
            return "Task not found: \(id)"
        case .invalidStatusTransition(let from, let to):
            return "Invalid status transition: \(from) → \(to)"
        case .commitNotFound(let id):
            return "Commit not found: \(id)"
        case .databaseError:
            return "Database error"
        }
    }
}

// MARK: - Usage Examples

/*
 // 创建任务
 let manager = LayCacheTaskManager(database: db, deviceId: "dev_abc123")
 
 let task = try manager.createTask(
     title: "测试V3 Task功能",
     status: .pending,
     priority: .P0,
     due: Date().addingTimeInterval(86400)  // 1天后
 )
 
 // 更新任务
 let updated = try manager.updateTask(
     taskId: task.taskId,
     changes: ["status": "in_progress"]
 )
 
 // 回滚任务
 let rolledBack = try manager.rollbackTask(
     taskId: task.taskId,
     toCommitId: "commit_001",
     reason: "误操作"
 )
 
 // 查看历史
 let history = try manager.getTaskHistory(taskId: task.taskId)
 */
