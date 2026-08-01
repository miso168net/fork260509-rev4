#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/wire-schema.py — 契約機器化：typings→JSON Schema 快照抽取（python 標準庫、單檔、自帶測試）

子命令：
  extract   base-web 容器內 npx 抽取 typings → draft-07 JSON Schema 快照，
            原子替換寫 rust-api/server/tests/fixtures/wire-schema.json（需 stack 在跑）
  check     重抽 typings 至暫存路徑、與工作樹快照 byte 比對（B-128 drift 閘；絕不覆寫
            快照）。--staged-gate＝pre-commit 專用收窄：staged base-web gitlink 區間零
            typings 變動即跳過。容器不可用＝警告＋0 放行；容器可用但重抽失敗／不一致＝2
  test      跑自帶測試（unittest、離線可跑）

失敗語意：stack 不在／抽取工具非零退出＝非零退出（2）＋stderr 提示啟動命令；抽取輸出
非合法 JSON＝不寫檔（防部分結果）；原子替換＝同目錄 temp 寫入後 os.replace；輸出確定性
（無產生時點欄位、同源重抽 byte 一致）。唯讀鐵則：npx 一次性、不碰 base-web 工作樹／
package.json／pnpm lock；前端 porcelain 前後皆空。用法錯誤走 exit 64（EX_USAGE）。

lineage：specs/003-wire-foundation/（契約＝contracts/contract-machinery.md §1、機器基準＝
data-model.md §3、抽取工具實測與釘版＝research.md R1）。
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

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


def extract_schema(run=_run_capture, hint=None):
    """跑容器內抽取 → 回 JSON Schema 文字（stdout）。

    失敗（docker 缺＝OSError／stack 不在＝非零退出）＝raise ExtractError（附補救提示）；
    絕不回部分結果。`run` 可注入（離線測試用）；`hint` 可覆寫提示尾巴——check 分支
    probe 已證容器可用、預設「起 stack」提示對其為無效補救、須換自屬句。"""
    argv = build_extract_argv()
    try:
        proc = run(argv)
    except OSError as ex:
        tail = hint or f"dev stack 未啟動？請先跑：{START_HINT}"
        raise ExtractError(f"無法執行 docker（{ex}）——{tail}")
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout or "").strip() or f"退出碼 {proc.returncode}"
        tail = hint or f"確認 dev stack 在跑：{START_HINT}"
        raise ExtractError(f"typings 抽取失敗（{reason}）——{tail}")
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
# check 子命令（B-128 快照 drift 閘）
# ---------------------------------------------------------------------------

# --staged-gate 收窄的 typings 抽取面（＝TYPINGS_GLOB 對應 pathspec）。
TYPINGS_PATHSPECS = ["src/typings/common.d.ts", "src/typings/api"]


def snapshots_match(fresh_bytes, snapshot_bytes):
    """byte 比對純函式（check 核心）——抽成純函式使入口 self-test 能餵相同／相異兩組
    合成 bytes、證紅綠俱可達（防恆綠）。"""
    return fresh_bytes == snapshot_bytes


def check_self_test():
    """check 入口無條件合成 self-test：相同 bytes 必判一致、相異必判不一致——失敗即
    比對邏輯壞（照 tools/fork-delta-lint.py main() 無條件 self_test 模式）。"""
    same = b'{"definitions":{"A":{"type":"object"}}}'
    other = b'{"definitions":{"B":{"type":"object"}}}'
    if not snapshots_match(same, same):
        raise AssertionError("相同 bytes 被誤判為不一致")
    if snapshots_match(same, other):
        raise AssertionError("相異 bytes 被誤判為一致")


def _clean_git_env(environ):
    """清掉 GIT_* env：git hook 會把外層 repo 的 GIT_DIR/GIT_INDEX_FILE 洩漏給子行程，
    害對 base-web worktree（.git 為檔）跑 git 抓錯 index（.git/index: Not a directory）
    ——照 tools/fork-delta-lint.py 現成模式。★僅用於對 base-web 的 git；外層
    git diff --cached 必須保留 env（commit -a 時 GIT_INDEX_FILE 指向暫時 index）。"""
    return {k: v for k, v in environ.items() if not k.startswith("GIT_")}


def _run_git_baseweb(argv):
    """對 base-web 跑 git（清 GIT_* env、cwd＝REPO_ROOT、-C 由 argv 自帶）。"""
    return subprocess.run(argv, capture_output=True, text=True, cwd=REPO_ROOT,
                          env=_clean_git_env(os.environ))


def probe_base_web(run=_run_capture):
    """base-web 容器可用性探測（容器內跑 true、廉價）。OSError／非零＝不可用。"""
    try:
        proc = run(BASE_WEB_EXEC + ["true"])
    except OSError:
        return False
    return proc.returncode == 0


def staged_typings_verdict(run_outer=_run_capture, run_baseweb=_run_git_baseweb):
    """--staged-gate 收窄判定（判定放 python、sh 只做粗判）。

    回傳四值：not-staged＝gitlink 未 staged（無事可查）；no-typings＝staged 區間零
    typings 變動；typings-changed＝有變動；unknown＝無法判定（保守走完整比對）。"""
    proc = run_outer(["git", "diff", "--cached", "--raw", "--no-abbrev", "--", "base-web"])
    if proc.returncode != 0:
        return "unknown"
    line = (proc.stdout or "").strip()
    if not line:
        return "not-staged"
    parts = line.split()
    if len(parts) < 4:
        return "unknown"
    old, new = parts[2], parts[3]
    if set(old) == {"0"} or set(new) == {"0"}:
        return "unknown"  # gitlink 新增／刪除——無區間可縮、走完整比對
    diff = run_baseweb(["git", "-C", "base-web", "diff", "--name-only", old, new, "--"]
                       + TYPINGS_PATHSPECS)
    if diff.returncode != 0:
        return "unknown"
    return "typings-changed" if (diff.stdout or "").strip() else "no-typings"


def cmd_check(staged_gate=False, run=_run_capture, run_outer=_run_capture,
              run_baseweb=_run_git_baseweb, output_path=OUTPUT_PATH):
    """check 子命令：重抽 typings 至暫存路徑、與工作樹快照 byte 比對（B-128 drift 閘）。

    絕不覆寫 OUTPUT_PATH；比對工作樹檔、勿讀 git blob（快照剛改未 commit 的中間態會誤紅）。
    fail 語意（user 親決 2026-08-01）：容器不可用→警告＋0 放行；容器可用但重抽失敗→2。"""
    # ① 無條件合成 self-test（防恆綠）。
    try:
        check_self_test()
    except AssertionError as ex:
        print(f"[check] ✗ self-test 失敗（check 比對邏輯壞）：{ex}", file=sys.stderr)
        return 2
    # ② hook 專用收窄：staged base-web gitlink 區間零 typings 變動＝跳過（省 npx 秒數）。
    if staged_gate:
        verdict = staged_typings_verdict(run_outer=run_outer, run_baseweb=run_baseweb)
        if verdict == "not-staged":
            print("[check] base-web gitlink 未 staged——無事可查、跳過")
            return 0
        if verdict == "no-typings":
            print("[check] staged base-web 區間零 typings 變動"
                  "（src/typings/common.d.ts＋src/typings/api/）——跳過重抽比對")
            return 0
        # typings-changed／unknown → 續跑完整比對。
    # ③ 容器探測：不可用＝警告＋放行（dev stack 未起不該擋無關 commit）。
    if not probe_base_web(run=run):
        print(f"[check] ⚠ base-web 容器不可用（stack 未起）——wire-schema check 跳過、放行；"
              f"要跑實比對先起 stack：{START_HINT}")
        return 0
    # ④ 重抽（容器宣稱可用、失敗即異常＝fail-loud，靜默跳過會成恆綠洞）。
    # ★提示尾巴自屬（勿沿用 extract 的「起 stack」句——probe 剛證容器可用、照打無效）：
    # 真因在容器內 npx 取件／typescript-json-schema 執行，補救＝手動重現抽取命令定位。
    check_hint = ("容器內手動重現抽取定位真因："
                  + " ".join(BASE_WEB_EXEC)
                  + f" sh -c '{build_npx_command()}'"
                  "；npm 取件失敗時檢查容器對 npm registry 連線")
    try:
        schema_text = extract_schema(run=run, hint=check_hint)
    except ExtractError as ex:
        print(f"[check] ✗ 容器可用但重抽失敗：{ex}", file=sys.stderr)
        return 2
    try:
        parsed = json.loads(schema_text)
    except json.JSONDecodeError as ex:
        print(f"[check] ✗ 容器可用但重抽輸出非合法 JSON（{ex}）", file=sys.stderr)
        return 2
    definitions = parsed.get("definitions") if isinstance(parsed, dict) else None
    if not isinstance(definitions, dict) or not definitions:
        print("[check] ✗ 重抽輸出缺非空 definitions 節（快照結構異常）", file=sys.stderr)
        return 2
    # ⑤ 暫存路徑落地（與 extract 同一 atomic_write 寫入路徑＝byte 語意一致）＋比對。
    tmp_dir = tempfile.mkdtemp(prefix="wire-schema-check.")
    try:
        tmp_path = os.path.join(tmp_dir, "wire-schema.json")
        atomic_write(tmp_path, schema_text)
        with open(tmp_path, "rb") as fh:
            fresh = fh.read()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    snap_abs = output_path if os.path.isabs(output_path) else os.path.join(REPO_ROOT, output_path)
    try:
        with open(snap_abs, "rb") as fh:
            on_disk = fh.read()
    except FileNotFoundError:
        print(f"[check] ✗ 快照檔缺席（{output_path}）——補救：python3 tools/wire-schema.py extract",
              file=sys.stderr)
        return 2
    if snapshots_match(fresh, on_disk):
        print(f"[check] ✓ 快照與 typings 重抽 byte 一致（{len(definitions)} definitions）")
        return 0
    # ★補救程序照兩段式 commit 真實走法寫（快照住 rust-api worktree、typings 住 base-web
    # worktree、分屬不同 repo——「同一 commit 提交兩者」跨 submodule 不可能照做；本閘正是
    # 為「pin 進了、快照沒進」而立，補救文字本身就是防復發教材）。
    print(f"[check] ✗ 快照與 typings 重抽不一致（{output_path}）——補救：先跑 "
          "python3 tools/wire-schema.py extract 重抽、rust-api worktree 內 commit 快照，"
          "再回外層同一 commit 一併 bump base-web 與 rust-api 兩支 pin",
          file=sys.stderr)
    return 2


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


class TestSnapshotsMatch(unittest.TestCase):
    """check 比對純函式紅綠（B-128；亦為入口合成 self-test 的直接對象）。"""

    def test_identical_bytes_match(self):
        payload = b'{"definitions":{"A":{}}}'
        self.assertTrue(snapshots_match(payload, payload))

    def test_different_bytes_mismatch(self):
        self.assertFalse(snapshots_match(
            b'{"definitions":{"A":{}}}', b'{"definitions":{"B":{}}}'))

    def test_check_self_test_passes_on_healthy_logic(self):
        check_self_test()  # 邏輯健康＝不 raise

    def test_check_self_test_failure_rc2(self):
        """★紅證另一半（防恆綠機制自身）：比對邏輯壞（恆回一致）時 check 入口
        self-test 必擋——rc 2、指名 check 比對邏輯壞、不觸任何子行程（與
        fork-delta-lint 同款無條件 self-test 對齊）。"""
        def boom(argv):
            raise AssertionError("self-test 失敗即 return 2、不得觸發任何子行程")

        err = io.StringIO()
        with unittest.mock.patch.object(
                sys.modules[__name__], "snapshots_match", lambda a, b: True):
            with contextlib.redirect_stderr(err):
                rc = cmd_check(run=boom, run_outer=boom, run_baseweb=boom)
        self.assertEqual(rc, 2)
        self.assertIn("self-test 失敗", err.getvalue())
        self.assertIn("比對邏輯壞", err.getvalue())


class TestCleanGitEnv(unittest.TestCase):
    """對 base-web 跑 git 前清 GIT_*（hook 洩漏外層 GIT_DIR/GIT_INDEX_FILE 撞 worktree index）。"""

    def test_strips_git_vars_keeps_rest(self):
        env = {"GIT_DIR": "/x/.git", "GIT_INDEX_FILE": "/x/idx",
               "GIT_WORK_TREE": "/x", "PATH": "/usr/bin", "HOME": "/home/u"}
        self.assertEqual(_clean_git_env(env), {"PATH": "/usr/bin", "HOME": "/home/u"})


class TestCheckFailOpen(unittest.TestCase):
    """容器不可用（stack 未起）＝警告＋rc 0 放行（user 親決 2026-08-01）。"""

    def test_container_unavailable_warns_and_passes(self):
        def fake_run(argv):
            return subprocess.CompletedProcess(
                argv, returncode=1, stdout="",
                stderr='service "base-web" is not running')

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cmd_check(run=fake_run)
        self.assertEqual(rc, 0)
        self.assertIn("wire-schema check 跳過", out.getvalue())
        self.assertIn("stack 未起", out.getvalue())

    def test_docker_missing_oserror_warns_and_passes(self):
        def fake_run(argv):
            raise FileNotFoundError("docker")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cmd_check(run=fake_run)
        self.assertEqual(rc, 0)
        self.assertIn("wire-schema check 跳過", out.getvalue())


class TestCheckFailLoud(unittest.TestCase):
    """容器可用但重抽失敗＝rc 2（環境宣稱可用時失敗即異常、靜默跳過＝恆綠洞）。"""

    @staticmethod
    def _probe_ok_extract(returncode, stdout="", stderr=""):
        def fake_run(argv):
            if argv[-1] == "true":  # 可用性探測
                return subprocess.CompletedProcess(argv, 0, "", "")
            return subprocess.CompletedProcess(argv, returncode, stdout, stderr)
        return fake_run

    def test_extract_nonzero_rc2(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            rc = cmd_check(run=self._probe_ok_extract(1, stderr="npx 非零退出"))
        self.assertEqual(rc, 2)
        self.assertIn("重抽失敗", err.getvalue())
        # ★提示自屬（勿夾帶 extract 的「起 stack」句——probe 剛證容器可用、自相矛盾）：
        # 補救＝容器內手動重現抽取命令。
        self.assertNotIn(START_HINT, err.getvalue())
        self.assertIn(build_npx_command(), err.getvalue())

    def test_extract_invalid_json_rc2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            rc = cmd_check(run=self._probe_ok_extract(0, stdout="not json"))
        self.assertEqual(rc, 2)

    def test_extract_empty_definitions_rc2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            rc = cmd_check(run=self._probe_ok_extract(0, stdout='{"definitions":{}}'))
        self.assertEqual(rc, 2)


class TestCheckCompare(unittest.TestCase):
    """重抽落暫存路徑 vs 工作樹快照 byte 比對——絕不覆寫快照、不一致指名補救命令。"""

    PAYLOAD = '{"$schema":"http://json-schema.org/draft-07/schema#","definitions":{"A":{}}}'

    def _fake_run(self, payload):
        def fake_run(argv):
            if argv[-1] == "true":
                return subprocess.CompletedProcess(argv, 0, "", "")
            return subprocess.CompletedProcess(argv, 0, payload, "")
        return fake_run

    def test_matching_snapshot_rc0_and_snapshot_untouched(self):
        with tempfile.TemporaryDirectory() as root:
            snap = os.path.join(root, "wire-schema.json")
            atomic_write(snap, self.PAYLOAD)
            with contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_check(run=self._fake_run(self.PAYLOAD), output_path=snap)
            self.assertEqual(rc, 0)
            with open(snap, encoding="utf-8") as fh:  # 快照原封不動
                self.assertEqual(fh.read(), self.PAYLOAD)

    def test_drifted_snapshot_rc2_names_remedy(self):
        with tempfile.TemporaryDirectory() as root:
            snap = os.path.join(root, "wire-schema.json")
            atomic_write(snap, self.PAYLOAD.replace('"A"', '"Z"'))
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = cmd_check(run=self._fake_run(self.PAYLOAD), output_path=snap)
            self.assertEqual(rc, 2)
            self.assertIn("python3 tools/wire-schema.py extract", err.getvalue())
            # 補救＝可照打的兩段式程序（快照與 typings 分屬兩 worktree、不可能同一
            # commit——正確走法：rust-api worktree commit 快照→外層一併 bump 兩支 pin）。
            self.assertIn("rust-api worktree 內 commit", err.getvalue())
            self.assertIn("bump base-web 與 rust-api 兩支 pin", err.getvalue())
            with open(snap, encoding="utf-8") as fh:  # 不一致也不得覆寫
                self.assertEqual(fh.read(), self.PAYLOAD.replace('"A"', '"Z"'))

    def test_missing_snapshot_rc2(self):
        with tempfile.TemporaryDirectory() as root:
            snap = os.path.join(root, "missing.json")
            with contextlib.redirect_stderr(io.StringIO()):
                rc = cmd_check(run=self._fake_run(self.PAYLOAD), output_path=snap)
            self.assertEqual(rc, 2)


_RAW_GITLINK = ":160000 160000 " + "a" * 40 + " " + "b" * 40 + " M\tbase-web\n"


class TestCheckStagedGate(unittest.TestCase):
    """--staged-gate 收窄（hook 專用）：未 staged／零 typings 變動＝跳過 rc 0、不觸容器。"""

    @staticmethod
    def _boom_run(argv):
        raise AssertionError("收窄應跳過、不得觸發容器探測／重抽")

    @staticmethod
    def _fixed(stdout, returncode=0):
        def fake(argv):
            return subprocess.CompletedProcess(argv, returncode, stdout, "")
        return fake

    def test_gitlink_not_staged_skips_rc0(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cmd_check(staged_gate=True, run=self._boom_run,
                           run_outer=self._fixed(""), run_baseweb=self._boom_run)
        self.assertEqual(rc, 0)
        self.assertIn("跳過", out.getvalue())

    def test_zero_typings_change_skips_rc0(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cmd_check(staged_gate=True, run=self._boom_run,
                           run_outer=self._fixed(_RAW_GITLINK),
                           run_baseweb=self._fixed(""))
        self.assertEqual(rc, 0)
        self.assertIn("跳過", out.getvalue())

    def test_typings_changed_runs_full_compare(self):
        payload = '{"definitions":{"A":{}}}'
        container_calls = []

        def spy_run(argv):
            container_calls.append(argv)
            if argv[-1] == "true":
                return subprocess.CompletedProcess(argv, 0, "", "")
            return subprocess.CompletedProcess(argv, 0, payload, "")

        with tempfile.TemporaryDirectory() as root:
            snap = os.path.join(root, "wire-schema.json")
            atomic_write(snap, payload)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cmd_check(staged_gate=True, run=spy_run,
                               run_outer=self._fixed(_RAW_GITLINK),
                               run_baseweb=self._fixed("src/typings/api/system.d.ts\n"),
                               output_path=snap)
        self.assertEqual(rc, 0)
        # ★可辨識斷言（跳過路徑 rc 同為 0、只驗 rc 釘不住正向面）：容器 seam 確被呼叫
        # （探測＋重抽共 2 次）、stdout 是完整比對的一致訊息而非跳過訊息。
        self.assertEqual(len(container_calls), 2)
        self.assertIn("byte 一致", out.getvalue())
        self.assertNotIn("跳過", out.getvalue())

    def test_zero_old_sha_verdict_unknown(self):
        raw = ":000000 160000 " + "0" * 40 + " " + "b" * 40 + " A\tbase-web\n"
        self.assertEqual(
            staged_typings_verdict(run_outer=self._fixed(raw),
                                   run_baseweb=self._boom_run),
            "unknown")

    def test_baseweb_diff_failure_verdict_unknown(self):
        self.assertEqual(
            staged_typings_verdict(run_outer=self._fixed(_RAW_GITLINK),
                                   run_baseweb=self._fixed("", returncode=128)),
            "unknown")

    def test_typings_pathspec_scopes_common_and_api(self):
        seen = {}

        def spy_baseweb(argv):
            seen["argv"] = argv
            return subprocess.CompletedProcess(argv, 0, "", "")

        staged_typings_verdict(run_outer=self._fixed(_RAW_GITLINK),
                               run_baseweb=spy_baseweb)
        self.assertIn("src/typings/common.d.ts", seen["argv"])
        self.assertIn("src/typings/api", seen["argv"])
        self.assertIn("base-web", seen["argv"])


class TestCheckUsage(unittest.TestCase):
    def test_check_rejects_unknown_flag_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["wire-schema.py", "check", "--bogus"]), 64)


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
    if cmd == "check":
        extra = [a for a in argv[2:] if a != "--staged-gate"]
        if extra:
            return usage(f"check：僅收 --staged-gate（見 {' '.join(extra)}）")
        return cmd_check(staged_gate="--staged-gate" in argv[2:])
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
