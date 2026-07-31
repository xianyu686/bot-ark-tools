#!/usr/bin/env python3
"""发版工具：一次命令同步版本号到 pyproject.toml + README 徽章 + README 当前版本文字。

用法:
    python bump_version.py 1.4.0
然后 git add/commit/push，再 build + 上传 PyPI（版本号已全部同步，不会再有徽章旧版问题）。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        print("用法: python bump_version.py <X.Y.Z>")
        return 1
    new = sys.argv[1]

    def read(p: Path) -> str:
        # newline='' 保留原行尾（Windows 下是 CRLF），避免写回造成 git 行尾噪音
        with p.open("r", encoding="utf-8", newline="") as f:
            return f.read()

    def write(p: Path, s: str) -> None:
        with p.open("w", encoding="utf-8", newline="") as f:
            f.write(s)

    # pyproject.toml: version = "x.y.z"
    py = read(PYPROJECT)
    py, n1 = re.subn(r'(?m)^version\s*=\s*"[^"]+"', f'version = "{new}"', py, count=1)
    if not n1:
        print("[x] pyproject.toml 找不到 version 行")
        return 1
    write(PYPROJECT, py)

    # README.md: 徽章 PyPI-<旧>-blue  +  当前版本：`<旧>`
    rd = read(README)
    rd, n2 = re.subn(r"PyPI-[\d.]+-blue", f"PyPI-{new}-blue", rd)
    rd, n3 = re.subn(r"当前版本：`[\d.]+`", f"当前版本：`{new}`", rd)
    if not n2 or not n3:
        print(f"[x] README 未匹配到徽章(n2={n2})或当前版本文字(n3={n3})")
        return 1
    write(README, rd)

    print(f"[OK] 版本已同步到 {new}:")
    print(f"  pyproject.toml version = {new}")
    print(f"  README 徽章 PyPI-{new}-blue")
    print(f"  README 当前版本：`{new}`")
    print("接下来: git add -A && git commit && git push，再 build/上传 PyPI。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
