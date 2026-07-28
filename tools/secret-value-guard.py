#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/secret-value-guard.py — 機密現值比對防線（019 U1；contracts/scan-gates.md §S2）

三層掃描防線的確定性層（僅外層 repo 掛載；源倉靠樣式層、零 python 依賴）：
讀機密現值 × 比對 staged 新增行，樣式掃描構不到的「裸值形」由本層攔截。

子命令：
  check   讀 $SECRETS_DIR（未設回退 deploy/secrets）下 *.txt 現值，比對
          `git diff --cached` 新增行；命中→exit 1、stderr 指名「檔案:行號＋機密名稱」、
          ★絕不輸出值本身（連遮蔽形都不印）。值目錄缺席或無合格值（開機未解密）→
          可辨識 skip 提示＋exit 0（fail-open；樣式掃描為主防線）。
          ★每次執行先跑紅綠 self-test（防恆綠）：紅樣本（執行期串接構造、防本檔自命中）
          未攔、近似綠樣本誤報、或 MIN_SECRET_LEN 邊界失守 → ERROR＋exit 1 擋 commit。
  test    跑自帶測試（unittest、離線、單檔零第三方依賴；先 purge_git_env 隔離 GIT_*）

退出碼：無命中 0（含合法 skip）；命中或 self-test 失敗 1；用法錯誤 64（usage 走 stderr）。
限制：值以單行比對（現值皆 printf '%s' 單行寫入）；binary diff 無文字面、不在本層射程。
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SECRETS_DIR = os.path.join("deploy", "secrets")
# 比對下界：短於此的現值不比對（誤報面失控；防線由樣式層接手）。
# ★self-test 的兩個邊界樣本用**字面長度**寫死、不由本常數構造：以被測常數自身構造＝套套
# 邏輯，常數一動樣本跟著動、兩檢查恆過（019 U1 實證：MIN 改 2 或 21，run_selftest() 皆
# True，而 pre-commit 生產面只跑 check→self-test，於是 MIN 落在 1~21 任一值時日常零守門）。
# 字面釘死後兩向都當場紅：MIN 被放寬→7 字元綠樣本誤報；MIN 被抬高→8 字元紅樣本未攔。
# ★因此下界一旦改動，必須同步改 EDGE_HIT／EDGE_SKIP（雙記帳、不得單邊改）。
MIN_SECRET_LEN = 8
EDGE_HIT = "E" * 8       # self-test 邊界紅樣本：恰達現行下界、必攔
EDGE_SKIP = "E" * 7      # self-test 邊界綠樣本：恰低於現行下界、不比對

RE_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def purge_git_env():
    """清掉本行程 GIT_* 環境變數（僅 test 子命令用；同 docs-sync 慣例）。

    git 跑 hook 時會把外層 repo 的 GIT_DIR／GIT_INDEX_FILE（絕對路徑）洩漏給子行程，
    測試 fixture 的 temp repo git 操作會因此寫進真 repo 的 index。
    ★check 生產面絕不可清：必須繼承 GIT_INDEX_FILE 才看得到 `git commit -a` 的臨時 index。
    """
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]


def eligible(value):
    """值是否納入比對（單行且長度達下界）。"""
    return len(value) >= MIN_SECRET_LEN and "\n" not in value and "\r" not in value


def load_secrets(secrets_dir):
    """讀機密現值：目錄下 *.txt（排除 *.example／子目錄）→ {名稱: 值}；目錄缺席回 {}。"""
    if not os.path.isdir(secrets_dir):
        return {}
    out = {}
    for name in sorted(os.listdir(secrets_dir)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(secrets_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            value = fh.read().rstrip("\r\n")
        out[name[:-len(".txt")]] = value
    return out


def staged_diff(root):
    """取 staged 內容（git diff --cached、零 context）；繼承 GIT_*（commit -a 臨時 index）。"""
    r = subprocess.run(["git", "-c", "core.quotepath=off", "diff", "--cached",
                        "--unified=0", "--no-color"],
                       cwd=root, capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        # fail-loud：git 面異常（非命中）——訊息可辨識、不靜默放行
        raise RuntimeError(f"git diff --cached 失敗（exit {r.returncode}）：{r.stderr.strip()}")
    return r.stdout


def find_hits(diff_text, secrets):
    """掃 unified diff 的新增行，回 [(路徑, 新檔行號, 機密名稱), …]；不看刪除行與 context。

    ★先以 hunk 邊界（RE_HUNK／`diff --git`）切開「檔頭區」與「內容區」，再判前綴：內容區
    的行前綴恆為 +／-／空白，故內容本身以「兩個加號」起頭的新增行會渲染成 `+++…`。單靠
    前綴同時判檔頭與新增行時，該行①含空白形 `+++ ` 被當成檔頭吃掉——path 被改寫成該行
    文字、後續命中報到錯的檔與錯的行；②無空白形 `+++x` 被 `not startswith("+++")` 整行
    排除——該行漏掃、且不推進行號，同 hunk 後續命中行號一併少算（019 U1 實證）。
    """
    hits = []
    path = None
    new_ln = 0
    in_hunk = False
    for line in diff_text.splitlines():
        m = RE_HUNK.match(line)
        if m:
            new_ln = int(m.group(1))
            in_hunk = True
            continue
        if line.startswith("diff --git "):
            in_hunk = False                # 下一個檔的檔頭區開始（內容行必帶前綴、撞不到）
            path = None
            continue
        if not in_hunk:                    # 檔頭區：只認 +++ 目標路徑
            if line.startswith("+++ "):
                target = line[4:].split("\t")[0]
                path = None if target == "/dev/null" else (
                    target[2:] if target.startswith("b/") else target)
            continue
        if line.startswith("+"):
            if path is not None:
                content = line[1:]
                for name, value in secrets.items():
                    if value in content:
                        hits.append((path, new_ln, name))
            new_ln += 1
        elif line.startswith("-"):
            continue                       # 舊行不佔新檔行號
        elif line.startswith(" "):
            new_ln += 1                    # context（-U0 下罕見）仍推進行號
    return hits


def _pipeline(diff_text, secrets):
    """比對管線＝eligible 過濾＋find_hits（check 與 self-test 共用同一條路）。"""
    return find_hits(diff_text, {n: v for n, v in secrets.items() if eligible(v)})


def run_selftest():
    """紅綠 self-test（每次 check 連帶跑；防恆綠）。全過回 True；否則印 ERROR 回 False。

    樣本全數執行期串接構造（防本檔自命中）；印錯誤只講樣本類別、不印樣本值。
    """
    ok = True
    v = "RV4" + "SELF" + "TEST" + "9f3a7c51d2"          # 長度遠超 MIN、單行
    red = _mk_diff("selftest.txt", ["x=" + v + ";"])
    if not _pipeline(red, {"selftest_secret": v}):
        print("[secret-value-guard] ERROR self-test：紅樣本未攔（防線恆綠）——擋 commit",
              file=sys.stderr)
        ok = False
    near = _mk_diff("selftest.txt", ["x=" + v[:-1] + "X" + ";"])   # 近似不命中
    if _pipeline(near, {"selftest_secret": v}):
        print("[secret-value-guard] ERROR self-test：綠樣本誤報（比對過寬）——擋 commit",
              file=sys.stderr)
        ok = False
    if not _pipeline(_mk_diff("selftest.txt", ["k=" + EDGE_HIT]), {"edge": EDGE_HIT}):
        print("[secret-value-guard] ERROR self-test：下界邊界紅樣本未攔（MIN_SECRET_LEN 被抬高？"
              "改下界須同步改 EDGE_HIT／EDGE_SKIP）——擋 commit", file=sys.stderr)
        ok = False
    if _pipeline(_mk_diff("selftest.txt", ["k=" + EDGE_SKIP]), {"edge": EDGE_SKIP}):
        print("[secret-value-guard] ERROR self-test：下界邊界綠樣本誤報（MIN_SECRET_LEN 被放寬？"
              "改下界須同步改 EDGE_HIT／EDGE_SKIP）——擋 commit", file=sys.stderr)
        ok = False
    return ok


def cmd_check():
    if not run_selftest():
        return 1
    sdir = os.environ.get("SECRETS_DIR") or DEFAULT_SECRETS_DIR
    if not os.path.isabs(sdir):
        sdir = os.path.join(ROOT, sdir)
    secrets = {n: v for n, v in load_secrets(sdir).items() if eligible(v)}
    if not secrets:
        print(f"[secret-value-guard] skip：機密現值目錄缺席或空（{sdir}）"
              "——比對層跳過（fail-open、樣式掃描為主防線）")
        return 0
    try:
        hits = find_hits(staged_diff(ROOT), secrets)
    except RuntimeError as ex:
        print(f"[secret-value-guard] ERROR {ex}——比對層本身異常、非機密命中", file=sys.stderr)
        return 1
    for path, ln, name in hits:
        print(f"[secret-value-guard] ✗ {path}:{ln} 含機密現值（{name}）"
              "——自 staged 移除後重試；本工具不印值（含遮蔽形）", file=sys.stderr)
    return 1 if hits else 0


# ---------------------------------------------------------------------------
# 測試工具
# ---------------------------------------------------------------------------

def _mk_diff(path, added_lines, start=1):
    """合成最小 unified diff（-U0 形）：path 新增 added_lines、新檔起始行號 start。"""
    n = len(added_lines)
    head = (f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n"
            f"+++ b/{path}\n"
            f"@@ -0,0 +{start},{n} @@\n")
    return head + "".join(f"+{l}\n" for l in added_lines)


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(d):
    _git(d, "init", "-q", "-b", "main")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")
    with open(os.path.join(d, "seed.txt"), "w", encoding="utf-8") as fh:
        fh.write("seed\n")
    _git(d, "add", "seed.txt")
    _git(d, "commit", "-qm", "init")


# 測試用假值：執行期串接構造（防本檔自命中被樣式層或值比對層誤攔）
def _fixture_value():
    return "ZX" + "42" + "fixture" + "value" + "99"


# ---------------------------------------------------------------------------
# 自帶測試（tools/secret-value-guard.py test）
# ---------------------------------------------------------------------------

class TestFindHits(unittest.TestCase):
    def test_hit_reports_file_and_line(self):
        v = _fixture_value()
        diff = _mk_diff("f.txt", ["clean line", "x=" + v + ";"], start=5)
        self.assertEqual(find_hits(diff, {"fake_key": v}), [("f.txt", 6, "fake_key")])

    def test_removed_and_context_lines_ignored(self):
        v = _fixture_value()
        diff = ("diff --git a/f.txt b/f.txt\n"
                "--- a/f.txt\n"
                "+++ b/f.txt\n"
                "@@ -1,2 +1,1 @@\n"
                f"-old {v} gone\n"
                " ctx " + v + " stays\n"
                "+fresh clean line\n")
        self.assertEqual(find_hits(diff, {"fake_key": v}), [])

    def test_multiple_files_and_hunks_line_numbers(self):
        v = _fixture_value()
        diff = (_mk_diff("a.txt", ["p", "q"], start=1)
                + _mk_diff("b.txt", ["r", v, "s"], start=10))
        self.assertEqual(find_hits(diff, {"k": v}), [("b.txt", 11, "k")])

    def test_near_miss_no_hit(self):
        v = _fixture_value()
        diff = _mk_diff("f.txt", ["x=" + v[:-1] + "Q"])
        self.assertEqual(find_hits(diff, {"k": v}), [])

    def test_added_line_starting_with_double_plus_space_is_content_not_header(self):
        """★內容以「兩個加號＋空白」起頭的新增行渲染成 `+++ …`：純前綴判檔頭會把它當檔頭
        吃掉，path 被改寫成該行文字（此樣本刻意偽裝成 `+++ b/evil.md`）、行號也不推進，
        於是命中報到錯的檔與錯的行。修前實測＝[('evil.md', 1, 'k')]。"""
        v = _fixture_value()
        diff = _mk_diff("f.md", ["++ b/evil.md", "x=" + v, "tail"])
        self.assertEqual(find_hits(diff, {"k": v}), [("f.md", 2, "k")])

    def test_added_line_starting_with_double_plus_is_scanned_and_counted(self):
        """★內容以「兩個加號」起頭（無空白）＝ diff 行 `+++x`：以 not startswith("+++")
        排除即該行整行漏掃，且不推進行號、同 hunk 後續命中行號少算 1。
        修前實測＝[('f.md', 1, 'k')]（首行漏掃＋次行行號少算）。"""
        v = _fixture_value()
        diff = _mk_diff("f.md", ["++" + v, "後續 " + v])
        self.assertEqual(find_hits(diff, {"k": v}),
                         [("f.md", 1, "k"), ("f.md", 2, "k")])

    def test_deleted_file_dev_null_target_skipped(self):
        v = _fixture_value()
        diff = ("diff --git a/gone.txt b/gone.txt\n"
                "--- a/gone.txt\n"
                "+++ /dev/null\n"
                "@@ -1,1 +0,0 @@\n"
                f"-{v}\n")
        self.assertEqual(find_hits(diff, {"k": v}), [])


class TestEligibleBoundary(unittest.TestCase):
    def test_min_len_value_is_eligible(self):
        self.assertTrue(eligible("B" * MIN_SECRET_LEN))

    def test_below_min_len_is_not(self):
        self.assertFalse(eligible("B" * (MIN_SECRET_LEN - 1)))

    def test_multiline_value_not_eligible(self):
        self.assertFalse(eligible("A" * MIN_SECRET_LEN + "\n" + "B" * MIN_SECRET_LEN))


class TestLoadSecrets(unittest.TestCase):
    def test_reads_txt_skips_example_and_readme(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            v = _fixture_value()
            for name, content in (("a.txt", v), ("a.txt.example", "CHANGE-ME-placeholder"),
                                  ("README.md", "說明")):
                with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                    fh.write(content)
            os.mkdir(os.path.join(d, "sub.txt"))   # 子目錄不讀
            self.assertEqual(load_secrets(d), {"a": v})

    def test_trailing_newline_stripped(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            v = _fixture_value()
            with open(os.path.join(d, "b.txt"), "w", encoding="utf-8") as fh:
                fh.write(v + "\r\n")
            self.assertEqual(load_secrets(d), {"b": v})

    def test_missing_dir_returns_empty(self):
        self.assertEqual(load_secrets("/nonexistent/rv4/secdir"), {})


class TestSelfTest(unittest.TestCase):
    def test_selftest_green_on_healthy_pipeline(self):
        self.assertTrue(run_selftest())

    def test_selftest_catches_dead_matcher(self):
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "find_hits", lambda *_a: []), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest())
        self.assertIn("紅樣本未攔", buf.getvalue())

    def test_selftest_catches_overeager_matcher(self):
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "find_hits",
                               lambda *_a: [("f.txt", 1, "x")]), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest())
        self.assertIn("綠樣本誤報", buf.getvalue())

    def test_selftest_catches_loosened_min_len(self):
        """放寬下界型突變（eligible 恆真）→ MIN-1 邊界綠樣本誤報、self-test 必紅。"""
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "eligible", lambda _v: True), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest())

    def test_selftest_catches_lowered_min_len_constant(self):
        """★下界常數被改小（MIN=2）→ 7 字元邊界綠樣本變成 eligible、誤報當場紅。
        邊界樣本若以 MIN_SECRET_LEN 自身構造即套套邏輯（常數一動樣本跟著動）：019 U1
        修前實測 MIN 改 2 時 run_selftest() 仍 True，生產面（pre-commit 只跑 check）零守門。"""
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "MIN_SECRET_LEN", 2), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest())
        self.assertIn("下界邊界綠樣本誤報", buf.getvalue())

    def test_selftest_catches_raised_min_len_constant(self):
        """★下界常數被抬高（MIN=21）→ 8 字元邊界紅樣本不再納入比對、未攔當場紅。
        修前實測 MIN 改 21 亦全綠，且同一支對 16 字元機密現值靜默跳過（掃描面失守）。"""
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "MIN_SECRET_LEN", 21), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest())
        self.assertIn("下界邊界紅樣本未攔", buf.getvalue())

    def test_selftest_never_prints_sample_values(self):
        import io, contextlib
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run_selftest()
        text = out.getvalue() + err.getvalue()
        self.assertNotIn("RV4" + "SELF" + "TEST", text)


class TestCmdCheckIntegration(unittest.TestCase):
    """git fixture 端到端（test 子命令入口已 purge_git_env、temp repo 不會寫真 index）。"""

    def _run_check(self, repo, secdir):
        import io, contextlib
        from unittest import mock
        mod = sys.modules[__name__]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(mod, "ROOT", repo), \
                mock.patch.dict(os.environ, {"SECRETS_DIR": secdir}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cmd_check()
        return rc, out.getvalue() + err.getvalue()

    def test_blocks_staged_secret_names_file_line_never_value(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = os.path.join(d, "repo")
            sec = os.path.join(d, "sec")
            os.makedirs(repo)
            os.makedirs(sec)
            _init_repo(repo)
            v = _fixture_value()
            with open(os.path.join(sec, "fake_key.txt"), "w", encoding="utf-8") as fh:
                fh.write(v)
            with open(os.path.join(repo, "leak.txt"), "w", encoding="utf-8") as fh:
                fh.write("prefix " + v + " suffix\n")
            _git(repo, "add", "leak.txt")
            rc, text = self._run_check(repo, sec)
            self.assertEqual(rc, 1)
            self.assertIn("leak.txt:1", text)
            self.assertIn("fake_key", text)
            self.assertNotIn(v, text)   # ★值本身絕不輸出（連遮蔽形都不印）

    def test_clean_staged_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = os.path.join(d, "repo")
            sec = os.path.join(d, "sec")
            os.makedirs(repo)
            os.makedirs(sec)
            _init_repo(repo)
            with open(os.path.join(sec, "fake_key.txt"), "w", encoding="utf-8") as fh:
                fh.write(_fixture_value())
            with open(os.path.join(repo, "ok.txt"), "w", encoding="utf-8") as fh:
                fh.write("nothing secret here\n")
            _git(repo, "add", "ok.txt")
            rc, _ = self._run_check(repo, sec)
            self.assertEqual(rc, 0)

    def test_missing_dir_skips_with_notice(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = os.path.join(d, "repo")
            os.makedirs(repo)
            _init_repo(repo)
            rc, text = self._run_check(repo, os.path.join(d, "nope"))
            self.assertEqual(rc, 0)
            self.assertIn("skip", text)

    def test_all_short_values_skips(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = os.path.join(d, "repo")
            sec = os.path.join(d, "sec")
            os.makedirs(repo)
            os.makedirs(sec)
            _init_repo(repo)
            with open(os.path.join(sec, "tiny.txt"), "w", encoding="utf-8") as fh:
                fh.write("B" * (MIN_SECRET_LEN - 1))
            rc, text = self._run_check(repo, sec)
            self.assertEqual(rc, 0)
            self.assertIn("skip", text)


class TestMainCli(unittest.TestCase):
    def _main(self, args):
        import io, contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            return main(["secret-value-guard"] + args)

    def test_no_args_usage_64(self):
        self.assertEqual(self._main([]), 64)

    def test_unknown_cmd_usage_64(self):
        self.assertEqual(self._main(["frobnicate"]), 64)

    def test_check_rejects_extra_args_64(self):
        self.assertEqual(self._main(["check", "--x"]), 64)

    def test_check_fails_when_selftest_red(self):
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        with mock.patch.object(mod, "run_selftest", lambda: False), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cmd_check(), 1)

    def test_test_branch_purges_git_env_and_only_there(self):
        """檔文釘住：main() 的 test 分支呼叫 purge_git_env、且全 main 僅此一處（check
        生產面清掉 GIT_* 會看不到 commit -a 的臨時 index）。"""
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(r"\ndef main\(argv\):\n(.*?)\n\nif __name__", src, re.S)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).count("purge_git_env()"), 1)
        self.assertIn('if cmd == "test":', m.group(1))


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def usage(msg=None):
    """用法錯誤：usage 走 stderr、exit 64（EX_USAGE；沿 018 家族慣例）。"""
    if msg:
        print(msg, file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 64


def main(argv):
    if len(argv) < 2:
        return usage()
    cmd = argv[1]
    if cmd == "test":
        purge_git_env()
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    if cmd == "check":
        if argv[2:]:
            return usage(f"check：不收參數（見 {' '.join(argv[2:])}）")
        return cmd_check()
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
