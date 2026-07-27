#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/wire-schema.py — 契約機器化：typings→JSON Schema 快照抽取（python 標準庫、單檔、自帶測試）

子命令：
  extract   base-web 容器內 npx 抽取 typings → draft-07 JSON Schema 快照，
            原子替換寫 rust-api/server/tests/fixtures/wire-schema.json（需 stack 在跑）
  test      跑自帶測試（unittest、離線可跑）

失敗語意：stack 不在／抽取工具非零退出＝非零退出（2）＋stderr 提示啟動命令；抽取輸出
非合法 JSON＝不寫檔（防部分結果）；原子替換＝同目錄 temp 寫入後 os.replace；輸出確定性
（無產生時點欄位、同源重抽 byte 一致）。唯讀鐵則：npx 一次性、不碰 base-web 工作樹／
package.json／pnpm lock；前端 porcelain 前後皆空。用法錯誤走 exit 64（EX_USAGE）。

lineage：specs/003-wire-foundation/（契約＝contracts/contract-machinery.md §1、機器基準＝
data-model.md §3、抽取工具實測與釘版＝research.md R1）。
"""
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 抽取工具釘版（research R1；npx 一次性、不進任何 manifest）。
TSJS_VERSION = "0.67.4"
# typings 抽取檔集（research R1：api 四檔＋common.d.ts 的 utility 命名空間）。
TYPINGS_GLOB = "src/typings/{common,api/*}.d.ts"
# 抽取型別選擇（全型別）與旗標（容忍 .d.ts 單編噪音＋required 欄完整）。
TSJS_TYPE = "*"
TSJS_FLAGS = ["--ignoreErrors", "--required"]

# base-web 容器內執行前綴：dev stack 的 base-web 服務、cwd＝/app。
COMPOSE = ["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.dev.yml"]
BASE_WEB_EXEC = COMPOSE + ["exec", "-T", "-w", "/app", "base-web"]

# 快照輸出路徑（追蹤、隨 rust-api worktree；data-model §3）。
OUTPUT_PATH = os.path.join("rust-api", "server", "tests", "fixtures", "wire-schema.json")

# stack 啟動提示（fail-loud 補救命令）。
START_HINT = "docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d"


class ExtractError(Exception):
    """抽取失敗（stack 不在／docker 缺／npx 非零）——走非零退出、絕不寫部分結果。"""


def build_npx_command():
    """組裝容器內 npx 抽取命令字串（釘版、檔集、型別、旗標——research R1 逐字）。"""
    return (
        f'npx -y typescript-json-schema@{TSJS_VERSION} '
        f'"{TYPINGS_GLOB}" "{TSJS_TYPE}" ' + " ".join(TSJS_FLAGS)
    )


def build_extract_argv():
    """完整 docker compose exec argv：base-web 容器 /app cwd 跑 `sh -c '<npx>'`。"""
    return BASE_WEB_EXEC + ["sh", "-c", build_npx_command()]


def _run_capture(argv):
    """跑 argv、capture stdout/stderr（text）；回 subprocess.CompletedProcess。"""
    return subprocess.run(argv, capture_output=True, text=True, cwd=REPO_ROOT)


def extract_schema(run=_run_capture):
    """跑容器內抽取 → 回 JSON Schema 文字（stdout）。

    失敗（docker 缺＝OSError／stack 不在＝非零退出）＝raise ExtractError（附啟動提示）；
    絕不回部分結果。`run` 可注入（離線測試用）。"""
    argv = build_extract_argv()
    try:
        proc = run(argv)
    except OSError as ex:
        raise ExtractError(
            f"無法執行 docker（{ex}）——dev stack 未啟動？請先跑：{START_HINT}"
        )
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout or "").strip() or f"退出碼 {proc.returncode}"
        raise ExtractError(
            f"typings 抽取失敗（{reason}）——確認 dev stack 在跑：{START_HINT}"
        )
    return proc.stdout


def atomic_write(path, content):
    """原子替換：同目錄 temp 寫入後 os.replace——絕不留部分結果／temp 殘留。"""
    abs_path = path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)
    directory = os.path.dirname(abs_path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".wire-schema.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.replace(tmp, abs_path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def cmd_extract():
    """extract 子命令：抽取 → 驗合法 JSON → 原子替換寫 OUTPUT_PATH。

    成功 0；stack 不在／npx 非零／輸出非 JSON＝2＋stderr 指名原因與補救命令。"""
    try:
        schema_text = extract_schema()
    except ExtractError as ex:
        print(f"[extract] {ex}", file=sys.stderr)
        return 2
    try:
        parsed = json.loads(schema_text)
    except json.JSONDecodeError as ex:
        print(f"[extract] 抽取輸出非合法 JSON（{ex}）——不寫檔（防部分結果）", file=sys.stderr)
        return 2
    definitions = parsed.get("definitions") if isinstance(parsed, dict) else None
    if not isinstance(definitions, dict) or not definitions:
        print("[extract] 抽取輸出缺非空 definitions 節（draft-07 快照結構異常）——不寫檔",
              file=sys.stderr)
        return 2
    atomic_write(OUTPUT_PATH, schema_text)
    print(f"[extract] 快照已寫入 {OUTPUT_PATH}（{len(definitions)} definitions）")
    return 0


# ---------------------------------------------------------------------------
# 自帶測試（unittest、離線可跑——不觸 docker）
# ---------------------------------------------------------------------------


class TestCommandAssembly(unittest.TestCase):
    def test_npx_command_pins_version_fileset_type_flags(self):
        cmd = build_npx_command()
        self.assertIn(f"typescript-json-schema@{TSJS_VERSION}", cmd)
        self.assertIn(f'"{TYPINGS_GLOB}"', cmd)
        self.assertIn(f'"{TSJS_TYPE}"', cmd)
        self.assertIn("--ignoreErrors", cmd)
        self.assertIn("--required", cmd)
        # 完整逐字（釘版契約＝research R1 實測命令形）。
        self.assertEqual(
            cmd,
            'npx -y typescript-json-schema@0.67.4 '
            '"src/typings/{common,api/*}.d.ts" "*" --ignoreErrors --required',
        )

    def test_extract_argv_targets_base_web_app_cwd(self):
        argv = build_extract_argv()
        self.assertEqual(argv[: len(BASE_WEB_EXEC)], BASE_WEB_EXEC)
        self.assertIn("-w", argv)
        self.assertIn("/app", argv)
        self.assertIn("base-web", argv)
        # 容器內以 sh -c 執行組裝好的 npx 命令。
        self.assertEqual(argv[-3:], ["sh", "-c", build_npx_command()])


class TestOutputPath(unittest.TestCase):
    def test_output_path_is_fixtures_wire_schema_json(self):
        self.assertEqual(
            OUTPUT_PATH,
            os.path.join("rust-api", "server", "tests", "fixtures", "wire-schema.json"),
        )


class TestExtractFailLoud(unittest.TestCase):
    def test_missing_stack_nonzero_raises_with_start_hint(self):
        def fake_run(argv):
            return subprocess.CompletedProcess(
                argv, returncode=1, stdout="",
                stderr="service \"base-web\" is not running",
            )

        with self.assertRaises(ExtractError) as cm:
            extract_schema(run=fake_run)
        self.assertIn("up", str(cm.exception))  # 提示啟動命令

    def test_docker_missing_oserror_raises_with_start_hint(self):
        def fake_run(argv):
            raise FileNotFoundError("docker")

        with self.assertRaises(ExtractError) as cm:
            extract_schema(run=fake_run)
        self.assertIn("docker", str(cm.exception))

    def test_success_returns_stdout_verbatim(self):
        payload = '{"$schema":"http://json-schema.org/draft-07/schema#","definitions":{}}'

        def fake_run(argv):
            return subprocess.CompletedProcess(
                argv, returncode=0, stdout=payload, stderr="npm warn ...",
            )

        self.assertEqual(extract_schema(run=fake_run), payload)


class TestAtomicWrite(unittest.TestCase):
    def test_atomic_write_creates_replaces_and_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "sub", "wire-schema.json")
            atomic_write(target, "hello")
            with open(target, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "hello")
            # 覆寫既有檔。
            atomic_write(target, "world")
            with open(target, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "world")
            # 無 .tmp 殘留（原子替換乾淨）。
            leftovers = [f for f in os.listdir(os.path.dirname(target)) if f.endswith(".tmp")]
            self.assertEqual(leftovers, [])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def usage(msg=None):
    """用法錯誤：usage 走 stderr、exit 64（EX_USAGE）。"""
    if msg:
        print(msg, file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 64


def main(argv):
    if len(argv) < 2:
        return usage()
    cmd = argv[1]
    if cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    if cmd == "extract":
        if argv[2:]:
            return usage(f"extract：不收參數（見 {' '.join(argv[2:])}）")
        return cmd_extract()
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
