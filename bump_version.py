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

    # pyproject.toml: version = "x.y.z"
    py = PYPROJECT.read_text(encoding="utf-8")
    py, n1 = re.subn(r'(?m)^version\s*=\s*"[^"]+"', f'version = "{new}"', py, count=1)
    if not n1:
        print("[x] pyproject.toml 找不到 version 行")
        return 1
    PYPROJECT.write_text(py, encoding="utf-8")

    # README.md: 徽章 PyPI-<旧>-blue  +  当前版本：`<旧>`
    rd = README.read_text(encoding="utf-8")
    rd, n2 = re.subn(r"PyPI-[\d.]+-blue", f"PyPI-{new}-blue", rd)
    rd, n3 = re.subn(r"当前版本：`[\d.]+`", f"当前版本：`{new}`", rd)
    if not n2 or not n3:
        print(f"[x] README 未匹配到徽章(n2={n2})或当前版本文字(n3={n3})")
        return 1
    README.write_text(rd, encoding="utf-8")

    print(f"[OK] 版本已同步到 {new}:")
    print(f"  pyproject.toml version = {new}")
    print(f"  README 徽章 PyPI-{new}-blue")
    print(f"  README 当前版本：`{new}`")
    print("接下来: git add -A && git commit && git push，再 build/上传 PyPI。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
