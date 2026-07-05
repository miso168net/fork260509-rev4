#!/usr/bin/env python3
"""PreToolUse(Workflow) 閘：script 缺 zh-TW 書面強制令 → 擋下（exit 2、stderr 回饋）。

根因＝L-113：sub-agent 不繼承主線 CLAUDE.md／session 語言紀律，未明令即預設英文
寫 report/blocker/程式碼註解。防線＝強制令必須逐字烤進 script 本體（防呆①②），
本 hook 為機器兜底。以 {name:...} 呼叫之預存 workflow 無 script 可驗→放行。
"""
import json
import os
import sys

def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # 輸入異常不擋（fail-open：本閘是兜底、非唯一防線）
    ti = data.get("tool_input") or {}
    content = ti.get("script") or ""
    sp = ti.get("scriptPath")
    if not content and sp and os.path.isfile(sp):
        try:
            with open(sp, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return 0
    if not content:  # name 式預存 workflow：無從驗、放行
        return 0
    if "zh-TW" in content:
        return 0
    sys.stderr.write(
        "[pre-workflow-gate] Workflow script 缺 zh-TW 書面強制令（CLAUDE.md §2 防呆①②、L-113）。"
        "把『★書面產物（report／blocker／程式碼註解／文件）一律 zh-TW』烤進每支 agent prompt 的"
        "不可違反項（INVARIANTS 模板字串）後再發射。"
    )
    return 2

if __name__ == "__main__":
    sys.exit(main())
