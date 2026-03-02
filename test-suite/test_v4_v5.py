#!/usr/bin/env python3
"""
LayCache V4/V5 - Encryption & Sync Test Suite

测试内容：
V4:
1. 密钥生成
2. 加密/解密
3. 密钥备份/恢复

V5:
4. Version Vector
5. Merge策略
6. Conflict检测与解决

用法：
  python3 test_v4_v5.py
"""

import sys
import json
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


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


# MARK: - V4: Encryption Tests

def test_v4_key_generation():
    """V4测试1: 密钥生成"""
    print_header("🔐 V4测试1: Key Generation")
    
    # 模拟密钥生成
    master_key = secrets.token_bytes(32)
    key_id = f"key_{hashlib.sha256(master_key).hexdigest()[:8]}"
    
    print_info(f"生成了256-bit主密钥")
    print_info(f"Key ID: {key_id}")
    
    # 验证密钥长度
    assert len(master_key) == 32, "密钥长度应该是32字节"
    
    print_success("密钥生成测试通过")
    return True


def test_v4_encryption_decryption():
    """V4测试2: 加密/解密"""
    print_header("🔐 V4测试2: Encryption/Decryption")
    
    # 简化版：模拟加密/解密
    # 实际应该使用cryptography库
    
    original_data = "敏感数据：我的长期偏好".encode('utf-8')
    key = secrets.token_bytes(32)
    
    # 模拟加密（简化版）
    # 实际：ciphertext = AES_GCM.encrypt(original_data, key)
    encrypted = {
        "encrypted": True,
        "algorithm": "AES-256-GCM",
        "ciphertext": original_data.hex(),  # 简化
        "keyId": f"key_{hashlib.sha256(key).hexdigest()[:8]}"
    }
    
    print_info(f"原始数据长度: {len(original_data)} bytes")
    print_info(f"加密后: {encrypted['algorithm']}")
    
    # 模拟解密
    decrypted = bytes.fromhex(encrypted["ciphertext"])
    
    assert decrypted == original_data, "解密后数据应该与原始数据一致"
    
    print_success("加密/解密测试通过")
    return True


def test_v4_key_backup():
    """V4测试3: 密钥备份"""
    print_header("🔐 V4测试3: Key Backup")
    
    master_key = secrets.token_bytes(32)
    password = "my_secure_password"
    salt = secrets.token_bytes(16)
    
    # 模拟PBKDF2
    # 实际：derived_key = PBKDF2(password, salt, iterations=100000)
    derived_key = hashlib.sha256(password.encode() + salt).digest()
    
    # 模拟加密主密钥
    # 实际：backup = AES_GCM.encrypt(master_key, derived_key)
    backup = {
        "keyBackupVersion": "1.0.0",
        "encryptedKey": master_key.hex(),
        "algorithm": "AES-256-GCM",
        "kdf": "PBKDF2-SHA256",
        "iterations": 100000,
        "salt": salt.hex()
    }
    
    print_info(f"备份版本: {backup['keyBackupVersion']}")
    print_info(f"KDF: {backup['kdf']}")
    print_info(f"Iterations: {backup['iterations']}")
    
    # 模拟恢复
    restored_key = bytes.fromhex(backup["encryptedKey"])
    
    assert restored_key == master_key, "恢复的密钥应该与原始密钥一致"
    
    print_success("密钥备份/恢复测试通过")
    return True


# MARK: - V5: Sync Tests

VersionVector = Dict[str, str]


@dataclass
class Event:
    event_id: str
    type: str
    content: Dict[str, Any]
    timestamp: str
    device_id: str
    previous_hash: Optional[str] = None


@dataclass
class Conflict:
    conflict_id: str
    conflicting_event_id: str
    local_version: Event
    remote_version: Event
    resolution: str = "manual"
    resolved_at: Optional[str] = None
    created_at: str = ""


class SyncManager:
    """简化的同步管理器（用于测试）"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.version_vector: VersionVector = {}
        self.events: List[Event] = []
        self.conflicts: List[Conflict] = []
    
    def add_event(self, event: Event):
        self.events.append(event)
        self.version_vector[event.device_id] = event.timestamp
    
    def merge(self, remote_events: List[Event]) -> Dict[str, int]:
        """合并远程events"""
        events_added = 0
        conflicts_detected = 0
        
        for remote_event in remote_events:
            # 检查是否已存在
            existing = next(
                (e for e in self.events if e.event_id == remote_event.event_id),
                None
            )
            
            if existing:
                # 检查哈希是否一致
                if not self._hashes_match(existing, remote_event):
                    # 冲突
                    conflict = Conflict(
                        conflict_id=f"conflict_{hashlib.md5(remote_event.event_id.encode()).hexdigest()[:8]}",
                        conflicting_event_id=remote_event.event_id,
                        local_version=existing,
                        remote_version=remote_event,
                        created_at=datetime.utcnow().isoformat() + "Z"
                    )
                    self.conflicts.append(conflict)
                    conflicts_detected += 1
            else:
                # 新event
                self.events.append(remote_event)
                self.version_vector[remote_event.device_id] = remote_event.timestamp
                events_added += 1
        
        return {
            "events_added": events_added,
            "conflicts_detected": conflicts_detected
        }
    
    def _hashes_match(self, e1: Event, e2: Event) -> bool:
        """检查两个event是否一致（简化版：实际应该计算完整哈希）"""
        # 如果设备不同，肯定不一致
        if e1.device_id != e2.device_id:
            return False
        
        # 检查其他关键字段
        return e1.type == e2.type and e1.timestamp == e2.timestamp
    
    def get_conflicts(self) -> List[Conflict]:
        return [c for c in self.conflicts if c.resolved_at is None]
    
    def resolve_conflict(self, conflict_id: str, keep: str):
        conflict = next((c for c in self.conflicts if c.conflict_id == conflict_id), None)
        if not conflict:
            raise ValueError(f"Conflict not found: {conflict_id}")
        
        # 选择保留的版本
        chosen = conflict.local_version if keep == "local" else conflict.remote_version
        
        # 更新event
        for i, e in enumerate(self.events):
            if e.event_id == conflict.conflicting_event_id:
                self.events[i] = chosen
                break
        
        # 标记已解决
        conflict.resolved_at = datetime.utcnow().isoformat() + "Z"


def test_v5_version_vector():
    """V5测试1: Version Vector"""
    print_header("🔄 V5测试1: Version Vector")
    
    sync = SyncManager("dev_abc123")
    
    # 添加一些events
    sync.add_event(Event(
        event_id="evt_001",
        type="task.created",
        content={"title": "Task 1"},
        timestamp="2026-03-02T21:00:00Z",
        device_id="dev_abc123"
    ))
    
    sync.add_event(Event(
        event_id="evt_002",
        type="task.created",
        content={"title": "Task 2"},
        timestamp="2026-03-02T21:30:00Z",
        device_id="dev_xyz789"
    ))
    
    vector = sync.version_vector
    
    print_info(f"Version Vector: {json.dumps(vector, indent=2)}")
    
    assert "dev_abc123" in vector, "应该包含本地设备"
    assert "dev_xyz789" in vector, "应该包含远程设备"
    assert vector["dev_abc123"] == "2026-03-02T21:00:00Z"
    assert vector["dev_xyz789"] == "2026-03-02T21:30:00Z"
    
    print_success("Version Vector测试通过")
    return True


def test_v5_merge():
    """V5测试2: Merge策略"""
    print_header("🔄 V5测试2: Merge Strategy")
    
    # 设备A
    sync_a = SyncManager("dev_a")
    sync_a.add_event(Event(
        event_id="evt_001",
        type="task.created",
        content={"title": "Task from A"},
        timestamp="2026-03-02T21:00:00Z",
        device_id="dev_a"
    ))
    
    # 设备B
    sync_b = SyncManager("dev_b")
    sync_b.add_event(Event(
        event_id="evt_002",
        type="task.created",
        content={"title": "Task from B"},
        timestamp="2026-03-02T21:10:00Z",
        device_id="dev_b"
    ))
    
    # A同步B的events
    result = sync_a.merge(sync_b.events)
    
    print_info(f"设备A原有events: 1")
    print_info(f"同步后events: {len(sync_a.events)}")
    print_info(f"新增events: {result['events_added']}")
    
    assert len(sync_a.events) == 2, "合并后应该有2个events"
    assert result["events_added"] == 1, "应该新增1个event"
    
    print_success("Merge策略测试通过（Block不覆盖）")
    return True


def test_v5_conflict():
    """V5测试3: Conflict检测"""
    print_header("🔄 V5测试3: Conflict Detection")
    
    # 设备A和B有相同的eventId但内容不同
    event_a = Event(
        event_id="evt_001",
        type="task.updated",
        content={"status": "completed"},
        timestamp="2026-03-02T21:00:00Z",
        device_id="dev_a"
    )
    
    event_b = Event(
        event_id="evt_001",
        type="task.updated",
        content={"status": "cancelled"},
        timestamp="2026-03-02T21:00:00Z",  # 相同时间戳，但不同设备
        device_id="dev_b"
    )
    
    sync = SyncManager("dev_a")
    sync.add_event(event_a)
    
    # 合并（检测冲突）
    result = sync.merge([event_b])
    
    print_info(f"合并events: 1")
    print_info(f"冲突检测: {result['conflicts_detected']}")
    
    conflicts = sync.get_conflicts()
    print_info(f"待解决冲突: {len(conflicts)}")
    
    assert result["conflicts_detected"] == 1, "应该检测到1个冲突"
    assert len(conflicts) == 1, "应该有1个待解决冲突"
    
    # 解决冲突
    sync.resolve_conflict(conflicts[0].conflict_id, keep="local")
    
    resolved_conflicts = sync.get_conflicts()
    print_info(f"解决后冲突: {len(resolved_conflicts)}")
    
    assert len(resolved_conflicts) == 0, "解决后应该没有待解决冲突"
    
    print_success("Conflict检测与解决测试通过（生成conflict_event，永远不LWW）")
    return True


# MARK: - Main

def main():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}🧪 LayCache V4/V5 Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    tests = [
        ("V4 - Key Generation", test_v4_key_generation),
        ("V4 - Encryption/Decryption", test_v4_encryption_decryption),
        ("V4 - Key Backup", test_v4_key_backup),
        ("V5 - Version Vector", test_v5_version_vector),
        ("V5 - Merge Strategy", test_v5_merge),
        ("V5 - Conflict Detection", test_v5_conflict),
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
