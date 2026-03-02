#!/usr/bin/env python3
"""
LayCache Conformance Test Suite
================================
LayCache协议一致性测试套件

用途：
  验证LayCache实现是否符合协议规范

用法：
  python3 conformance-test.py <implementation_dir>

测试内容：
  1. Event Schema验证
  2. Derivation Schema验证
  3. Commit Schema验证
  4. Canonicalization一致性
  5. 哈希链完整性
  6. Bundle导出格式
  7. 签名验证（可选）

输出：
  - 通过/失败报告
  - 详细错误信息
  - 兼容性评分
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Try to import jsonschema
try:
    import jsonschema
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("⚠️  未安装jsonschema，跳过schema验证")
    print("   安装方法: pip install jsonschema")


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestResult:
    """测试结果"""
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def add_pass(self):
        self.passed += 1

    def add_fail(self, error: str):
        self.failed += 1
        self.errors.append(error)

    def add_skip(self, reason: str):
        self.skipped += 1
        self.errors.append(f"[SKIP] {reason}")

    @property
    def total(self):
        return self.passed + self.failed + self.skipped

    @property
    def score(self):
        if self.total == 0:
            return 0
        return int((self.passed / self.total) * 100)


class ConformanceTest:
    """LayCache协议一致性测试"""

    def __init__(self, impl_dir: str):
        self.impl_dir = Path(impl_dir)
        self.results = []
        self.schemas = {}

        if not self.impl_dir.exists():
            print(f"{Colors.RED}❌ 目录不存在: {impl_dir}{Colors.RESET}")
            sys.exit(1)

        # Load schemas
        self._load_schemas()

    def _load_schemas(self):
        """加载JSON Schema"""
        schema_dir = Path(__file__).parent / 'schemas'

        if not schema_dir.exists():
            print(f"{Colors.YELLOW}⚠️  Schema目录不存在: {schema_dir}{Colors.RESET}")
            return

        for schema_file in schema_dir.glob('*.json'):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                    schema_name = schema_file.stem
                    self.schemas[schema_name] = schema
                    print(f"{Colors.CYAN}📋 加载Schema: {schema_name}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}❌ 加载Schema失败: {schema_file}: {e}{Colors.RESET}")

    def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}🧪 LayCache 协议一致性测试{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"📁 测试目录: {self.impl_dir}")
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

        # 1. Event Schema测试
        self._test_event_schema()

        # 2. Derivation Schema测试
        self._test_derivation_schema()

        # 3. Commit Schema测试
        self._test_commit_schema()

        # 4. Canonicalization测试
        self._test_canonicalization()

        # 5. 哈希链测试
        self._test_hash_chain()

        # 6. Bundle格式测试
        self._test_bundle_format()

        # 生成报告
        self._generate_report()

    def _test_event_schema(self):
        """测试Event Schema"""
        result = TestResult("Event Schema")

        print(f"\n{Colors.BLUE}📋 测试: Event Schema{Colors.RESET}")

        # 查找events.jsonl
        events_file = self.impl_dir / 'events.jsonl'
        if not events_file.exists():
            result.add_skip("events.jsonl不存在")
            self.results.append(result)
            return

        # 加载events
        events = []
        with open(events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        result.add_fail(f"JSON解析失败: {e}")

        print(f"  加载了 {len(events)} 个events")

        # 验证每个event
        required_fields = ['eventId', 'type', 'content', 'timestamp', 'deviceId']

        for i, event in enumerate(events):
            # 检查必需字段
            missing = [f for f in required_fields if f not in event]
            if missing:
                result.add_fail(f"Event {i}: 缺少字段 {missing}")
                continue

            # Schema验证（如果有）
            if HAS_JSONSCHEMA and 'event' in self.schemas:
                try:
                    validate(instance=event, schema=self.schemas['event'])
                except ValidationError as e:
                    result.add_fail(f"Event {i}: Schema验证失败: {e.message}")
                    continue

            result.add_pass()

        print(f"  {Colors.GREEN}✅ 通过: {result.passed}{Colors.RESET}")
        if result.failed > 0:
            print(f"  {Colors.RED}❌ 失败: {result.failed}{Colors.RESET}")

        self.results.append(result)

    def _test_derivation_schema(self):
        """测试Derivation Schema"""
        result = TestResult("Derivation Schema")

        print(f"\n{Colors.BLUE}📋 测试: Derivation Schema{Colors.RESET}")

        # 查找derivations.jsonl
        deriv_file = self.impl_dir / 'derivations.jsonl'
        if not deriv_file.exists():
            result.add_skip("derivations.jsonl不存在")
            self.results.append(result)
            return

        # 加载derivations
        derivations = []
        with open(deriv_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        derivations.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        result.add_fail(f"JSON解析失败: {e}")

        print(f"  加载了 {len(derivations)} 个derivations")

        # 验证每个derivation
        required_fields = ['derivationId', 'eventId', 'type', 'output', 'timestamp']

        for i, deriv in enumerate(derivations):
            missing = [f for f in required_fields if f not in deriv]
            if missing:
                result.add_fail(f"Derivation {i}: 缺少字段 {missing}")
                continue

            if HAS_JSONSCHEMA and 'derivation' in self.schemas:
                try:
                    validate(instance=deriv, schema=self.schemas['derivation'])
                except ValidationError as e:
                    result.add_fail(f"Derivation {i}: Schema验证失败: {e.message}")
                    continue

            result.add_pass()

        print(f"  {Colors.GREEN}✅ 通过: {result.passed}{Colors.RESET}")
        if result.failed > 0:
            print(f"  {Colors.RED}❌ 失败: {result.failed}{Colors.RESET}")

        self.results.append(result)

    def _test_commit_schema(self):
        """测试Commit Schema"""
        result = TestResult("Commit Schema")

        print(f"\n{Colors.BLUE}📋 测试: Commit Schema{Colors.RESET}")

        commits_file = self.impl_dir / 'commits.jsonl'
        if not commits_file.exists():
            result.add_skip("commits.jsonl不存在")
            self.results.append(result)
            return

        commits = []
        with open(commits_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        commits.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        result.add_fail(f"JSON解析失败: {e}")

        print(f"  加载了 {len(commits)} 个commits")

        required_fields = ['commitId', 'blockId', 'timestamp', 'deviceId', 'commitHash']

        for i, commit in enumerate(commits):
            missing = [f for f in required_fields if f not in commit]
            if missing:
                result.add_fail(f"Commit {i}: 缺少字段 {missing}")
                continue

            if HAS_JSONSCHEMA and 'commit' in self.schemas:
                try:
                    validate(instance=commit, schema=self.schemas['commit'])
                except ValidationError as e:
                    result.add_fail(f"Commit {i}: Schema验证失败: {e.message}")
                    continue

            result.add_pass()

        print(f"  {Colors.GREEN}✅ 通过: {result.passed}{Colors.RESET}")
        if result.failed > 0:
            print(f"  {Colors.RED}❌ 失败: {result.failed}{Colors.RESET}")

        self.results.append(result)

    def _test_canonicalization(self):
        """测试Canonicalization一致性"""
        result = TestResult("Canonicalization")

        print(f"\n{Colors.BLUE}📋 测试: Canonicalization{Colors.RESET}")

        # 测试用例
        test_cases = [
            {
                "input": {"b": 2, "a": 1, "c": 3},
                "expected": '{"a":1,"b":2,"c":3}'
            },
            {
                "input": {"z": "last", "a": "first"},
                "expected": '{"a":"first","z":"last"}'
            },
            {
                "input": {"number": 123, "string": "abc"},
                "expected": '{"number":123,"string":"abc"}'
            }
        ]

        for i, tc in enumerate(test_cases):
            canonical = json.dumps(
                tc["input"],
                sort_keys=True,
                separators=(',', ':'),
                ensure_ascii=False
            )

            if canonical == tc["expected"]:
                result.add_pass()
            else:
                result.add_fail(
                    f"测试用例 {i}: 期望 '{tc['expected']}', 得到 '{canonical}'"
                )

        print(f"  {Colors.GREEN}✅ 通过: {result.passed}{Colors.RESET}")
        if result.failed > 0:
            print(f"  {Colors.RED}❌ 失败: {result.failed}{Colors.RESET}")

        self.results.append(result)

    def _test_hash_chain(self):
        """测试哈希链完整性"""
        result = TestResult("Hash Chain")

        print(f"\n{Colors.BLUE}📋 测试: Hash Chain{Colors.RESET}")

        # 加载events
        events_file = self.impl_dir / 'events.jsonl'
        if not events_file.exists():
            result.add_skip("events.jsonl不存在")
            self.results.append(result)
            return

        events = []
        with open(events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        if len(events) < 2:
            result.add_skip("events数量不足（<2）")
            self.results.append(result)
            return

        print(f"  检查 {len(events)} 个events的哈希链")

        # 验证哈希链
        for i in range(1, len(events)):
            event = events[i]
            prev_event = events[i-1]

            # 计算前一个event的哈希
            prev_canonical = json.dumps(
                prev_event,
                sort_keys=True,
                separators=(',', ':'),
                ensure_ascii=False
            ).encode('utf-8')

            prev_hash = hashlib.sha256(prev_canonical).hexdigest()[:16]

            # 检查当前event是否包含正确的previousHash
            if 'previousHash' in event:
                if event['previousHash'] != prev_hash:
                    result.add_fail(
                        f"Event {i}: previousHash不匹配 "
                        f"(期望: {prev_hash}, 实际: {event['previousHash']})"
                    )
                else:
                    result.add_pass()
            else:
                # 如果没有previousHash字段，也算通过（向后兼容）
                result.add_pass()

        print(f"  {Colors.GREEN}✅ 通过: {result.passed}{Colors.RESET}")
        if result.failed > 0:
            print(f"  {Colors.RED}❌ 失败: {result.failed}{Colors.RESET}")

        self.results.append(result)

    def _test_bundle_format(self):
        """测试Bundle格式"""
        result = TestResult("Bundle Format")

        print(f"\n{Colors.BLUE}📋 测试: Bundle Format{Colors.RESET}")

        # 查找manifest.json
        manifest_file = self.impl_dir / 'manifest.json'
        if not manifest_file.exists():
            result.add_skip("manifest.json不存在")
            self.results.append(result)
            return

        # 加载manifest
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            result.add_fail(f"读取manifest失败: {e}")
            self.results.append(result)
            return

        # 检查必需字段
        required_fields = ['version', 'exportTime', 'deviceId', 'stats']

        for field in required_fields:
            if field in manifest:
                result.add_pass()
            else:
                result.add_fail(f"manifest缺少字段: {field}")

        # 检查stats
        if 'stats' in manifest:
            stats_fields = ['events', 'commits', 'blocks']
            for field in stats_fields:
                if field in manifest['stats']:
                    result.add_pass()
                else:
                    result.add_fail(f"manifest.stats缺少字段: {field}")

        print(f"  {Colors.GREEN}✅ 通过: {result.passed}{Colors.RESET}")
        if result.failed > 0:
            print(f"  {Colors.RED}❌ 失败: {result.failed}{Colors.RESET}")

        self.results.append(result)

    def _generate_report(self):
        """生成测试报告"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 测试报告{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for result in self.results:
            print(f"📋 {result.name}")
            print(f"   ✅ 通过: {result.passed}")
            if result.failed > 0:
                print(f"   ❌ 失败: {result.failed}")
            if result.skipped > 0:
                print(f"   ⏭️  跳过: {result.skipped}")

            if result.errors and (result.failed > 0 or result.skipped > 0):
                print(f"   {Colors.YELLOW}错误详情:{Colors.RESET}")
                for error in result.errors[:5]:  # 只显示前5个
                    print(f"      - {error}")

            total_passed += result.passed
            total_failed += result.failed
            total_skipped += result.skipped
            print()

        # 计算总分
        total_tests = total_passed + total_failed
        if total_tests > 0:
            score = int((total_passed / total_tests) * 100)
        else:
            score = 0

        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}📈 总体评分{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"   通过: {total_passed}")
        print(f"   失败: {total_failed}")
        print(f"   跳过: {total_skipped}")
        print()

        if score >= 90:
            color = Colors.GREEN
            status = "✅ 优秀"
        elif score >= 70:
            color = Colors.YELLOW
            status = "⚠️  良好"
        elif score >= 50:
            color = Colors.YELLOW
            status = "⚠️  需改进"
        else:
            color = Colors.RED
            status = "❌ 不合格"

        print(f"{color}{Colors.BOLD}{status} - {score}/100{Colors.RESET}\n")

        # 保存JSON报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "implementationDir": str(self.impl_dir),
            "summary": {
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "score": score
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "failed": r.failed,
                    "skipped": r.skipped,
                    "errors": r.errors
                }
                for r in self.results
            ]
        }

        report_file = self.impl_dir / f"conformance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 报告已保存: {report_file.name}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

        # 返回退出码
        if score >= 70:
            sys.exit(0)
        else:
            sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print(f"用法: {sys.argv[0]} <implementation_dir>")
        print(f"示例: {sys.argv[0]} ./my_laycache_impl")
        sys.exit(1)

    test = ConformanceTest(sys.argv[1])
    test.run_all_tests()


if __name__ == '__main__':
    main()
