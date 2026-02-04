from __future__ import annotations

import csv
import json
import mimetypes
from dataclasses import dataclass, field
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class DataStore:
    tasks: list[dict] = field(default_factory=list)
    repair_order: dict = field(default_factory=dict)
    user_permissions: list[dict] = field(default_factory=list)
    devices: list[dict] = field(default_factory=list)


STORE = DataStore(
    tasks=[
        {
            "id": 1001,
            "room": "A1",
            "device": "UPS",
            "serial_number": "UPS-A1-8892",
            "priority": 1,
            "status": "待处理",
            "engineer": "张工",
            "scheduled_date": date.today().isoformat(),
            "notes": "UPS 电池组温度偏高。",
        },
        {
            "id": 1002,
            "room": "B2",
            "device": "空调主机",
            "serial_number": "AC-B2-2201",
            "priority": 2,
            "status": "进行中",
            "engineer": "李工",
            "scheduled_date": date.today().isoformat(),
            "notes": "检查冷凝水排放异常。",
        },
        {
            "id": 1003,
            "room": "C3",
            "device": "配电柜",
            "serial_number": "PDU-C3-1108",
            "priority": 3,
            "status": "待处理",
            "engineer": "王工",
            "scheduled_date": date.today().isoformat(),
            "notes": "巡检发现断路器温升。",
        },
    ],
    repair_order={
        "strategy": "按优先级 + 计划时间排序",
        "notes": "优先级 1 为最高，跨班组任务可手动调整。",
    },
    user_permissions=[
        {
            "role": "管理员",
            "permissions": ["配置权限", "维护计划", "审核工单", "查看报表"],
        },
        {
            "role": "班组长",
            "permissions": ["分配任务", "调整顺序", "查看所有工单"],
        },
        {
            "role": "工程师",
            "permissions": ["查看今日任务", "更新工单状态"],
        },
    ],
    devices=[
        {
            "serial_number": "UPS-A1-8892",
            "device": "UPS",
            "room": "A1",
            "cabinet": "A1-01",
            "u_position": "16U",
            "owner": "核心供电",
        },
        {
            "serial_number": "AC-B2-2201",
            "device": "空调主机",
            "room": "B2",
            "cabinet": "B2-温控",
            "u_position": "机柜外",
            "owner": "环境控制",
        },
        {
            "serial_number": "PDU-C3-1108",
            "device": "配电柜",
            "room": "C3",
            "cabinet": "C3-02",
            "u_position": "24U",
            "owner": "动力配电",
        },
    ],
)


class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _parse_csv_payload(self, payload: str) -> list[dict]:
        reader = csv.DictReader(StringIO(payload))
        rows = []
        for row in reader:
            normalized = {key.strip(): (value or "").strip() for key, value in row.items()}
            if normalized.get("serial_number"):
                rows.append(normalized)
        return rows

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_file(BASE_DIR / "templates" / "admin.html")
            return
        if parsed.path == "/admin":
            self._send_file(BASE_DIR / "templates" / "admin.html")
            return
        if parsed.path == "/engineer":
            self._send_file(BASE_DIR / "templates" / "engineer.html")
            return
        if parsed.path.startswith("/static/"):
            self._send_file(BASE_DIR / parsed.path.lstrip("/"))
            return
        if parsed.path == "/api/tasks/today":
            today = date.today().isoformat()
            tasks = [task for task in STORE.tasks if task["scheduled_date"] == today]
            self._send_json({"date": today, "tasks": tasks})
            return
        if parsed.path == "/api/repair-order":
            self._send_json(STORE.repair_order)
            return
        if parsed.path == "/api/permissions":
            self._send_json(STORE.user_permissions)
            return
        if parsed.path == "/api/devices":
            self._send_json({"devices": STORE.devices})
            return
        if parsed.path == "/api/devices/lookup":
            query = parse_qs(parsed.query)
            serial = (query.get("serial") or [""])[0].strip()
            match = next(
                (device for device in STORE.devices if device["serial_number"] == serial),
                None,
            )
            self._send_json({"serial": serial, "device": match})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path == "/api/repair-order":
            payload = self._parse_json()
            STORE.repair_order.update(
                {
                    "strategy": payload.get("strategy", STORE.repair_order["strategy"]),
                    "notes": payload.get("notes", STORE.repair_order["notes"]),
                }
            )
            self._send_json(STORE.repair_order)
            return
        if parsed.path == "/api/permissions":
            payload = self._parse_json()
            role = payload.get("role")
            permissions = payload.get("permissions")
            if role and permissions:
                STORE.user_permissions.append(
                    {"role": role, "permissions": permissions}
                )
            self._send_json(STORE.user_permissions)
            return
        if parsed.path == "/api/devices/bulk":
            payload = self._parse_json()
            devices = payload.get("devices", [])
            if not devices and "csv" in payload:
                devices = self._parse_csv_payload(payload.get("csv", ""))
            if devices:
                STORE.devices = devices
            self._send_json({"devices": STORE.devices})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")


def run_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    server = HTTPServer((host, port), RequestHandler)
    print(f"Server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
