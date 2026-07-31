"""纯净 HTTP 微服务：任何 bot 框架 / 网页 / 脚本都能调用（零额外依赖）。

启动：ark-tools server --port 8899
接口：
  GET  /banners                        卡池列表
  POST /gacha/pull                     {"user_id","banner","count"}
  GET  /operator?name=能天使          干员信息
  GET  /archive?name=能天使           档案
  GET  /voice?name=能天使             语音
  GET  /story?keyword=0-10            剧情
  POST /recruit                       {"user_id","tags"}
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from ak_core import ArkCore

CORE = ArkCore()


class Handler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            return {}

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        path = url.path.rstrip("/")
        try:
            if path == "/banners":
                self._json({"ok": True, "banners": CORE.list_banners()})
            elif path == "/operator":
                op = CORE.operator_card(q.get("name", [""])[0])
                self._json({"ok": bool(op), "data": op})
            elif path == "/archive":
                a = CORE.get_archive(q.get("name", [""])[0])
                self._json({"ok": bool(a), "data": a})
            elif path == "/voice":
                v = CORE.get_voice(q.get("name", [""])[0])
                self._json({"ok": bool(v), "data": v})
            elif path == "/story":
                s = CORE.get_story(q.get("keyword", [""])[0])
                self._json({"ok": bool(s), "data": s})
            elif path == "/health":
                self._json({"ok": True, "ready": CORE.store.ready()})
            else:
                self._json({"ok": False, "error": "not found"}, 404)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        body = self._read_body()
        try:
            if path == "/gacha/pull":
                r = CORE.pull(body.get("user_id", ""), body.get("banner"), int(body.get("count", 1)))
                self._json({"ok": r.get("ok", False), "error": r.get("error"), "data": r})
            elif path == "/recruit":
                r = CORE.recruit(body.get("user_id", ""), body.get("tags", ""))
                self._json({"ok": r.get("ok", False), "error": r.get("error"), "data": r})
            else:
                self._json({"ok": False, "error": "not found"}, 404)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def log_message(self, fmt, *args):
        pass  # 静默日志


def run_server(host: str = "127.0.0.1", port: int = 8899):
    print(f"[ark-tools] HTTP server running: http://{host}:{port}")
    print("  GET /banners | POST /gacha/pull | GET /operator?name=X | GET /archive?name=X")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run_server()
