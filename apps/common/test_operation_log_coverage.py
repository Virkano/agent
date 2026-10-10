import ast
import re
from pathlib import Path

from django.test import SimpleTestCase

from common.log.labels import MENU_LABELS, OPERATE_LABELS, expand_menu_labels
from system_manage.models import Log
from xpack_lite.views.operate_log import _serialize_log


APPS_DIR = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    *sorted((APPS_DIR / "marketing" / "views").glob("*.py")),
    APPS_DIR / "platform_monitoring" / "views.py",
    APPS_DIR / "rehearsal" / "views.py",
    APPS_DIR / "tools" / "views" / "api_orchestration.py",
    APPS_DIR / "trigger" / "views" / "event_orchestration.py",
    APPS_DIR / "trigger" / "views" / "resource_coordination.py",
    APPS_DIR / "knowledge" / "views" / "etl.py",
    APPS_DIR / "knowledge" / "views" / "evaluation.py",
    APPS_DIR / "application" / "views" / "answer_review.py",
    APPS_DIR / "models_provider" / "views" / "lifecycle.py",
    APPS_DIR / "models_provider" / "views" / "pipeline.py",
]
CHINESE = re.compile(r"[\u4e00-\u9fff]")


def _decorator_name(decorator):
    expression = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return expression.attr
    return None


def _has_log_decorator(method):
    return any(_decorator_name(decorator) == "log" for decorator in method.decorator_list)


class OperationLogCoverageTests(SimpleTestCase):
    def test_new_module_mutations_and_file_exports_have_global_logs(self):
        missing = []
        for path in TARGET_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                owner = next(
                    (
                        class_node.name
                        for class_node in ast.walk(tree)
                        if isinstance(class_node, ast.ClassDef) and node in class_node.body
                    ),
                    "<module>",
                )
                is_mutation = node.name in {"post", "put", "patch", "delete"}
                is_file_operation = node.name == "get" and re.search(r"Export|Download", owner)
                if (is_mutation or is_file_operation) and not _has_log_decorator(node):
                    missing.append(f"{path.relative_to(APPS_DIR)}:{node.lineno} {owner}.{node.name}")
        self.assertEqual(missing, [])

    def test_every_english_decorator_label_has_a_chinese_normalization(self):
        missing = []
        for path in APPS_DIR.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or _decorator_name(node) != "log":
                    continue
                for keyword in node.keywords:
                    if keyword.arg not in {"menu", "operate"}:
                        continue
                    if not isinstance(keyword.value, ast.Constant) or not isinstance(keyword.value.value, str):
                        continue
                    value = keyword.value.value
                    labels = MENU_LABELS if keyword.arg == "menu" else OPERATE_LABELS
                    if not CHINESE.search(value) and value not in labels:
                        missing.append(f"{path.relative_to(APPS_DIR)}:{node.lineno} {keyword.arg}={value}")
        self.assertEqual(missing, [])

    def test_legacy_english_log_is_serialized_in_chinese(self):
        item = Log(menu="Application", operate="Create an application", user={"id": "actor-1"})
        serialized = _serialize_log(item)
        self.assertEqual(serialized["menu_label"], "智能体")
        self.assertEqual(serialized["operate"], "创建智能体")

    def test_chinese_menu_filter_includes_legacy_and_current_values(self):
        self.assertEqual(expand_menu_labels(["智能体"]), {"智能体", "Application"})
