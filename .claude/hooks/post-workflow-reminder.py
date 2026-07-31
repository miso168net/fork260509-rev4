#!/usr/bin/env python3
"""PostToolUse(Workflow) 提醒：Workflow 剛發射 → 注入看門狗原子成對提醒（L-112）。

hook 無從查驗同回合是否已有 Monitor call（無 harness 狀態可見性），故為提醒層；
硬規則住 CLAUDE.md §2（launch 與 Monitor 同一回合原子成對）。additionalContext
會隨工具結果注入主線 context——正好落在失誤點。
"""
import json
import sys

def main() -> int:
    try:
        json.load(sys.stdin)  # 消化輸入（內容不需）
    except Exception:
        pass
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "⚠️ Workflow 已發射——看門狗 Monitor 必須與 launch 同一回合原子成對"
                "（CLAUDE.md §2、L-112）。若本回合尚未掛：立即以 Monitor"
                "（command: bash tools/wf-watchdog.sh <冒煙token>）補掛、再做其他事。"
                "完成通知一到→TaskStop 該 Monitor。"
            ),
        }
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
