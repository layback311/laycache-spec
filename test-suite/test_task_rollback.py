#!/usr/bin/env python3
"""
LayCache V3 - Task & Rollback Test Suite

测试内容：
1. Task CRUD操作
2. Task Event记录
3. 状态机验证
4. 回滚语义测试

用法：
  python3 test_task_rollback.py
"""

import sys
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


# MARK: - Enums

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    @property
    def valid_transitions(self) -> List['TaskStatus']:
        transitions = {
            TaskStatus.PENDING: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [TaskStatus.PENDING, TaskStatus.COMPLETED, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [],  # 终态
            TaskStatus.CANCELLED: [TaskStatus.PENDING],
        }
        return transitions.get(self, [])


class TaskPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


# MARK: - Colors

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{msg}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")


# MARK: - Task Manager (In-Memory for Testing)

class TaskManager:
    """简单的内存Task管理器，用于测试"""
    
    def __init__(self, device_id: str = "dev_test01"):
        self.device_id = device_id
        self.tasks: Dict[str, Dict] = {}
        self.task_events: List[Dict] = []
        self.commits: Dict[str, Dict] = {}
    
    def create_task(
        self,
        title: str,
        status: TaskStatus = TaskStatus.PENDING,
        priority: TaskPriority = TaskPriority.P2,
        due: Optional[datetime] = None,
        source_refs: Optional[List[str]] = None
    ) -> Dict:
        """创建任务"""
        task_id = f"task_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        
        task = {
            "taskId": task_id,
            "title": title,
            "status": status.value,
            "priority": priority.value,
            "due": due.isoformat() + "Z" if due else None,
            "sourceRefs": source_refs,
            "createdAt": now,
            "updatedAt": now,
            "deviceId": self.device_id
        }
        
        self.tasks[task_id] = task
        
        # 记录事件
        commit_id = f"commit_{hashlib.md5((task_id + now).encode()).hexdigest()[:8]}"
        
        # 计算previousHash（第一个事件为None）
        previous_hash = None
        if self.task_events:
            prev_event = self.task_events[-1]
            prev_canonical = json.dumps(
                prev_event,
                sort_keys=True,
                separators=(',', ':'),
                ensure_ascii=False
            ).encode('utf-8')
            previous_hash = hashlib.sha256(prev_canonical).hexdigest()[:16]
        
        event = {
            "eventId": f"evt_{hashlib.md5((task_id + 'created').encode()).hexdigest()[:8]}",
            "eventType": "task.created",
            "taskId": task_id,
            "content": {
                "title": title,
                "status": status.value,
                "priority": priority.value
            },
            "timestamp": now,
            "deviceId": self.device_id,
            "commitId": commit_id,
            "previousHash": previous_hash
        }
        
        self.task_events.append(event)
        self.commits[commit_id] = event
        
        return task
    
    def update_task(self, task_id: str, changes: Dict[str, Any]) -> Dict:
        """更新任务"""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        old_status = TaskStatus(task["status"])
        
        # 检查状态转换
        if "status" in changes:
            new_status = TaskStatus(changes["status"])
            if new_status not in old_status.valid_transitions:
                raise ValueError(
                    f"Invalid status transition: {old_status.value} → {new_status.value}"
                )
        
        # 更新字段
        for key, value in changes.items():
            if key in task:
                task[key] = value
        
        task["updatedAt"] = datetime.utcnow().isoformat() + "Z"
        
        # 记录事件
        commit_id = f"commit_{hashlib.md5((task_id + task['updatedAt']).encode()).hexdigest()[:8]}"
        
        # 先计算previousHash（使用最后一个事件）
        previous_hash = None
        if self.task_events:
            prev_event = self.task_events[-1]
            prev_canonical = json.dumps(
                prev_event,
                sort_keys=True,
                separators=(',', ':'),
                ensure_ascii=False
            ).encode('utf-8')
            previous_hash = hashlib.sha256(prev_canonical).hexdigest()[:16]
        
        event = {
            "eventId": f"evt_{hashlib.md5((task_id + 'update' + task['updatedAt']).encode()).hexdigest()[:8]}",
            "eventType": "task.updated",
            "taskId": task_id,
            "content": changes,
            "timestamp": task["updatedAt"],
            "deviceId": self.device_id,
            "commitId": commit_id,
            "previousHash": previous_hash
        }
        
        self.task_events.append(event)
        self.commits[commit_id] = event
        
        return task
    
    def rollback_task(self, task_id: str, to_commit_id: str, reason: Optional[str] = None) -> Dict:
        """回滚任务"""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        if to_commit_id not in self.commits:
            raise ValueError(f"Commit not found: {to_commit_id}")
        
        # 获取目标commit
        target_commit = self.commits[to_commit_id]
        
        # 找到需要回滚的commits
        commits_to_reverse = []
        for event in reversed(self.task_events):
            if event["taskId"] == task_id:
                if event["commitId"] == to_commit_id:
                    break
                commits_to_reverse.append(event)
        
        # 记录rollback事件
        now = datetime.utcnow().isoformat() + "Z"
        rollback_commit_id = f"commit_rollback_{hashlib.md5((task_id + now).encode()).hexdigest()[:8]}"
        
        rollback_event = {
            "eventId": f"evt_rollback_{hashlib.md5((task_id + now).encode()).hexdigest()[:8]}",
            "eventType": "task.rollback",
            "taskId": task_id,
            "content": {
                "rollbackTo": to_commit_id,
                "rollbackFrom": self.task_events[-1]["commitId"] if self.task_events else None,
                "reversedCommits": [c["commitId"] for c in commits_to_reverse],
                "reason": reason
            },
            "timestamp": now,
            "deviceId": self.device_id,
            "commitId": rollback_commit_id,
            "previousHash": hashlib.sha256(
                json.dumps(self.task_events[-1], sort_keys=True).encode()
            ).hexdigest()[:16] if self.task_events else None
        }
        
        self.task_events.append(rollback_event)
        self.commits[rollback_commit_id] = rollback_event
        
        self.tasks[task_id]["updatedAt"] = now
        
        return self.tasks[task_id]
    
    def get_task_history(self, task_id: str) -> List[Dict]:
        """获取任务历史"""
        return [e for e in self.task_events if e["taskId"] == task_id]


# MARK: - Tests

def test_task_creation():
    """测试1: 任务创建"""
    print_header("📋 测试1: Task Creation")
    
    manager = TaskManager()
    
    task = manager.create_task(
        title="测试V3 Task功能",
        status=TaskStatus.PENDING,
        priority=TaskPriority.P0,
        due=datetime.utcnow() + timedelta(days=1)
    )
    
    print_info(f"Created task: {task['taskId']}")
    print_info(f"Title: {task['title']}")
    print_info(f"Status: {task['status']}")
    print_info(f"Priority: {task['priority']}")
    
    # 验证事件记录
    events = manager.get_task_history(task['taskId'])
    assert len(events) == 1, "应该有1个事件"
    assert events[0]['eventType'] == 'task.created', "事件类型应该是task.created"
    
    print_success("Task创建测试通过")
    return True


def test_status_transitions():
    """测试2: 状态转换"""
    print_header("📋 测试2: Status Transitions")
    
    manager = TaskManager()
    task = manager.create_task(title="测试状态转换")
    
    # 合法转换: pending → in_progress
    try:
        manager.update_task(task['taskId'], {"status": "in_progress"})
        print_success("pending → in_progress: 合法")
    except ValueError as e:
        print_error(f"合法转换被拒绝: {e}")
        return False
    
    # 合法转换: in_progress → completed
    try:
        manager.update_task(task['taskId'], {"status": "completed"})
        print_success("in_progress → completed: 合法")
    except ValueError as e:
        print_error(f"合法转换被拒绝: {e}")
        return False
    
    # 非法转换: completed → pending (终态不可逆转)
    try:
        manager.update_task(task['taskId'], {"status": "pending"})
        print_error("completed → pending: 应该被拒绝但通过了")
        return False
    except ValueError as e:
        print_success(f"completed → pending: 正确拒绝 ({e})")
    
    print_success("状态转换测试通过")
    return True


def test_rollback():
    """测试3: 回滚语义"""
    print_header("📋 测试3: Rollback Semantics")
    
    manager = TaskManager()
    
    # 1. 创建任务 (commit_1)
    task = manager.create_task(
        title="测试回滚",
        status=TaskStatus.PENDING,
        priority=TaskPriority.P2
    )
    commit_1 = manager.task_events[-1]['commitId']
    print_info(f"创建任务: commit_1 = {commit_1}")
    
    # 2. 更新任务 (commit_2)
    manager.update_task(task['taskId'], {"status": "in_progress"})
    commit_2 = manager.task_events[-1]['commitId']
    print_info(f"更新状态: commit_2 = {commit_2}")
    
    # 3. 再次更新 (commit_3)
    manager.update_task(task['taskId'], {"priority": "P0"})
    commit_3 = manager.task_events[-1]['commitId']
    print_info(f"更新优先级: commit_3 = {commit_3}")
    
    # 验证当前状态
    assert task['status'] == "in_progress", "状态应该是in_progress"
    assert task['priority'] == "P0", "优先级应该是P0"
    
    # 4. 回滚到 commit_2
    print_info("回滚到 commit_2...")
    rolled_back = manager.rollback_task(
        task['taskId'],
        to_commit_id=commit_2,
        reason="测试回滚"
    )
    
    # 5. 验证回滚
    events = manager.get_task_history(task['taskId'])
    print_info(f"历史事件数: {len(events)}")
    
    # 应该有: created, update(status), update(priority), rollback
    assert len(events) == 4, f"应该有4个事件，实际{len(events)}"
    
    # 最后一个事件应该是rollback
    last_event = events[-1]
    assert last_event['eventType'] == 'task.rollback', "最后一个事件应该是rollback"
    assert last_event['content']['rollbackTo'] == commit_2, "应该回滚到commit_2"
    
    print_success(f"回滚测试通过")
    print_success(f"  - 回滚前事件数: 3")
    print_success(f"  - 回滚后事件数: 4 (append-only)")
    print_success(f"  - 历史完整保留")
    
    return True


def test_append_only():
    """测试4: Append-Only规则"""
    print_header("📋 测试4: Append-Only Rule")
    
    manager = TaskManager()
    
    # 创建并多次更新
    task = manager.create_task(title="测试Append-Only")
    manager.update_task(task['taskId'], {"priority": "P1"})
    manager.update_task(task['taskId'], {"status": "in_progress"})
    
    # 回滚
    commit_1 = manager.task_events[0]['commitId']
    manager.rollback_task(task['taskId'], to_commit_id=commit_1)
    
    # 验证：所有事件都存在
    events = manager.get_task_history(task['taskId'])
    
    print_info(f"总事件数: {len(events)}")
    for i, event in enumerate(events):
        print(f"  {i+1}. {event['eventType']} @ {event['timestamp'][:19]}")
    
    # 没有任何事件被删除
    event_types = [e['eventType'] for e in events]
    assert 'task.created' in event_types, "created事件应该存在"
    assert 'task.updated' in event_types, "updated事件应该存在"
    assert 'task.rollback' in event_types, "rollback事件应该存在"
    
    print_success("Append-Only规则测试通过")
    print_success("  - 所有历史事件保留")
    print_success("  - 回滚不删除历史")
    
    return True


def test_event_chain():
    """测试5: 事件链完整性"""
    print_header("📋 测试5: Event Chain Integrity")
    
    manager = TaskManager()
    
    # 创建多个事件
    task = manager.create_task(title="测试事件链")
    manager.update_task(task['taskId'], {"priority": "P1"})
    manager.update_task(task['taskId'], {"status": "in_progress"})
    
    events = manager.get_task_history(task['taskId'])
    
    # 验证哈希链
    for i in range(1, len(events)):
        current = events[i]
        previous = events[i-1]
        
        # 计算前一个事件的哈希
        prev_canonical = json.dumps(
            previous,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False
        ).encode('utf-8')
        
        expected_hash = hashlib.sha256(prev_canonical).hexdigest()[:16]
        actual_hash = current.get('previousHash')
        
        if actual_hash != expected_hash:
            print_error(f"事件{i}的previousHash不匹配")
            print_error(f"  期望: {expected_hash}")
            print_error(f"  实际: {actual_hash}")
            return False
    
    print_success("事件链完整性测试通过")
    print_success(f"  - 验证了{len(events)-1}个previousHash")
    print_success("  - 所有哈希匹配")
    
    return True


# MARK: - Main

def main():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}🧪 LayCache V3 - Task & Rollback Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    tests = [
        ("Task Creation", test_task_creation),
        ("Status Transitions", test_status_transitions),
        ("Rollback Semantics", test_rollback),
        ("Append-Only Rule", test_append_only),
        ("Event Chain Integrity", test_event_chain),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} 失败: {e}")
            results.append((name, False))
    
    # 总结
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 测试总结{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: 通过")
        else:
            print_error(f"{name}: 失败")
    
    print(f"\n{Colors.BOLD}总计: {passed}/{total} 通过{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ 部分测试失败{Colors.RESET}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
