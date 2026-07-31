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
          ★旗標 --full-tree（B-118）：同源讀值、改掃 `git ls-files` 全 tracked 檔逐行
          bytes 比對（binary＝含 NUL byte 者跳過）——staged 增量對「既存於 tracked 檔的
          現值」結構性失明（L-190），本模式供導入時盤點與定期體檢；命中→stderr 只印
          「檔案:行號｜機密名」。★不接進 pre-commit（全樹非增量、成本未拍板）。
  test    跑自帶測試（unittest、離線、單檔零第三方依賴；先 purge_git_env 隔離 GIT_*）

退出碼：無命中 0（含合法 skip）；命中或 self-test 失敗 1；用法錯誤 64（usage 走 stderr）。
限制：值以單行比對（現值皆 printf '%s' 單行寫入）；binary diff／binary 檔無文字面、
不在本層射程。
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
# .env 行形偵測＝**寬樣式**（019 U4 quality 修；六處解析器同刀齊改）：compose 的 .env
# 解析器接受 UTF-8 BOM／行首空白／export 前綴／等號兩側空白／CRLF 行尾。行首錨定
# `SECRETS_DIR=` 的窄樣式對這五形一律漏認並**靜默回退** repo 內舊落點——本層於是改掃
# 空目錄、印 skip 且 rc=0，裸值格結構性失守而全綠（＝L-174 經另一條路復發）。
# 寬進窄出：寬樣式撈出 compose 會讀到的那一行，值再套下方嚴格白名單。
RE_ENV_SECRETS_DIR = re.compile(
    r"^[ \t]*(?:export[ \t]+)?SECRETS_DIR[ \t]*=[ \t]*(.*?)[ \t]*$")
# .env 值字元白名單：與 deploy 四腳本 case 樣式 `*[!A-Za-z0-9_/.-]*` 逐字同集合。
RE_ENV_VALUE_OK = re.compile(r"^[A-Za-z0-9_/.-]+$")


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


def resolve_secrets_dir(root, env=None):
    """機密落點三級口徑（與 deploy 四腳本同口徑；019 契約 §P5.1／P5.2 第五消費者）。

    環境變數優先（與 compose 口徑一致）→ repo 根 `.env` 只嚴格解析 `SECRETS_DIR` 一行
    → 皆缺回退 repo 內 `deploy/secrets`。
    ★不整檔 source／不引 dotenv：compose 的 `.env` 允許不加引號的含空白值、井號語意亦與
    shell 不同。★`.env` 有該鍵但值非法＝**吵鬧失敗**（回錯誤訊息）而非靜默回退——靜默回退
    會讓本層改掃 repo 內舊落點、明明沒在守卻回綠（假綠）。
    ★**行形偵測寬、值校驗窄**（019 U4）：偵測面必須涵蓋 compose 會讀到的每一種行形
    （BOM／縮排／export 前綴／等號兩側空白／CRLF），否則漏認即靜默回退＝同一個假綠。
    ★**空字串邊界**（019 U4 quality）：「已匯出但為空」≠「未設」——shell 環境已勝出 `.env`，
    compose 的 `${SECRETS_DIR:-./deploy/secrets}` 對空字串直接吃預設值、回退 repo 內舊落點
    且**不讀 `.env` 該鍵**；`if val:` 把空字串當未設而續讀 `.env`＝本層掃新落點、compose
    掛舊落點的靜默分裂。空字串無合法用途（要走回退請 unset），故吵鬧失敗指名真因。
    回 `(絕對路徑, None)` 或 `(None, 錯誤訊息)`。
    """
    env = os.environ if env is None else env
    val = env.get("SECRETS_DIR")
    if val == "":
        return None, ("SECRETS_DIR 已匯出為空字串——compose 會忽略 .env 並回退 repo 內 "
                      "./deploy/secrets；要用 .env 的值請先 unset SECRETS_DIR")
    if val:
        return (val if os.path.isabs(val) else os.path.join(root, val)), None
    envfile = os.path.join(root, ".env")
    if os.path.isfile(envfile):
        raw_val = None
        # utf-8-sig＝剝首行 UTF-8 BOM（compose 同口徑；Windows 側編輯器覆存常見）
        with open(envfile, encoding="utf-8-sig", errors="replace") as fh:
            for raw in fh:
                m = RE_ENV_SECRETS_DIR.match(raw.rstrip("\r\n"))
                if m:
                    raw_val = m.group(1)   # 取最後一筆（同腳本 `grep … | tail -n 1`）
        if raw_val is not None:
            if not RE_ENV_VALUE_OK.match(raw_val):
                return None, (".env 之 SECRETS_DIR 為空或含空白／shell 元字元"
                              "——拒用（產檔約束見 .env.example）")
            if not raw_val.startswith("/"):
                return None, (".env 之 SECRETS_DIR 必須為絕對路徑字面"
                              "（compose 不做 shell 展開）——見 .env.example")
            return raw_val, None
    return os.path.join(root, DEFAULT_SECRETS_DIR), None


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
    sdir, err = resolve_secrets_dir(ROOT)
    if err is not None:
        print(f"[secret-value-guard] ERROR {err}——比對層本身異常、非機密命中", file=sys.stderr)
        return 1
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
# B-118 全樹盤點模式（check --full-tree）
# ---------------------------------------------------------------------------

def tracked_files(root):
    """全 tracked 檔相對路徑清單（`git ls-files -z -s`、只取 blob）；異常→RuntimeError。

    ★濾除 mode 160000（gitlink＝submodule pin）：外層對其無 blob 內容、worktree 上是
    目錄——不濾則每跑必對兩 submodule 誤印「讀不到…不視同乾淨」WARN（結構性噪音）。
    """
    r = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "-z", "-s"],
                       cwd=root, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git ls-files 失敗（exit {r.returncode}）："
                           f"{r.stderr.decode('utf-8', 'replace').strip()}")
    out = []
    for entry in r.stdout.decode("utf-8", "replace").split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)     # 「mode sha stage\t路徑」
        if meta.split(" ", 1)[0] != "160000":
            out.append(path)
    return out


def scan_tree_lines(content, secrets):
    """單檔全內容掃描：bytes 逐行比對（不經解碼、編碼異常構不成炸點）→ [(行號, 機密名), …]。

    binary（含 NUL byte）→ 回 None＝跳過（無文字面；同 git 判 binary 的實務慣例）。
    行以 b"\\n" 切分＝CRLF 行尾不影響行號（現值經 eligible 過濾必為單行、不含 CR，
    行尾殘留的 b"\\r" 不干擾子串比對）。整檔載入：本 repo tracked 檔皆小、簡單為上。
    """
    if b"\0" in content:
        return None
    hits = []
    enc = [(name, value.encode("utf-8")) for name, value in sorted(secrets.items())]
    for ln, line in enumerate(content.split(b"\n"), start=1):
        for name, vb in enc:
            if vb in line:
                hits.append((ln, name))
    return hits


def run_selftest_full_tree():
    """全樹模式紅綠 self-test（每次 --full-tree 先跑；防恆綠、同 check 慣例）。

    樣本執行期串接構造（防本檔自命中）；印錯誤只講樣本類別、不印樣本值。
    """
    ok = True
    v = "RV4" + "TREE" + "TEST" + "8c2d91ab4e"
    sec = {"selftest_secret": v}
    if scan_tree_lines(("頭\nx=" + v + ";\n").encode("utf-8"), sec) != \
            [(2, "selftest_secret")]:
        print("[secret-value-guard] ERROR self-test：全樹紅樣本未攔或行號錯（防線恆綠）"
              "——中止盤點", file=sys.stderr)
        ok = False
    if scan_tree_lines(("x=" + v[:-1] + "X\n").encode("utf-8"), sec):
        print("[secret-value-guard] ERROR self-test：全樹綠樣本誤報（比對過寬）——中止盤點",
              file=sys.stderr)
        ok = False
    if scan_tree_lines(b"\x00" + v.encode("utf-8"), sec) is not None:
        print("[secret-value-guard] ERROR self-test：binary 樣本未跳過——中止盤點",
              file=sys.stderr)
        ok = False
    return ok


def cmd_full_tree():
    """B-118 一次性全樹盤點：機密現值 × 全 tracked 檔逐行比對；讀值與 check 同源。"""
    if not run_selftest_full_tree():
        return 1
    sdir, err = resolve_secrets_dir(ROOT)
    if err is not None:
        print(f"[secret-value-guard] ERROR {err}——比對層本身異常、非機密命中", file=sys.stderr)
        return 1
    secrets = {n: v for n, v in load_secrets(sdir).items() if eligible(v)}
    if not secrets:
        print(f"[secret-value-guard] skip：機密現值目錄缺席或空（{sdir}）"
              "——全樹盤點跳過（fail-open、樣式掃描為主防線）")
        return 0
    try:
        files = tracked_files(ROOT)
    except RuntimeError as ex:
        print(f"[secret-value-guard] ERROR {ex}——比對層本身異常、非機密命中", file=sys.stderr)
        return 1
    n_hit = n_bin = 0
    for rel in files:
        try:
            with open(os.path.join(ROOT, rel), "rb") as fh:
                content = fh.read()
        except OSError:
            print(f"[secret-value-guard] WARN 讀不到 {rel}——略過（不視同乾淨）",
                  file=sys.stderr)
            continue
        hits = scan_tree_lines(content, secrets)
        if hits is None:
            n_bin += 1
            continue
        for ln, name in hits:
            n_hit += 1
            print(f"[secret-value-guard] ✗ {rel}:{ln}｜{name}"
                  "——tracked 檔含機密現值；本工具不印值（含遮蔽形）", file=sys.stderr)
    print(f"[secret-value-guard] 全樹盤點：掃 {len(files)} 支 tracked 檔"
          f"（binary 跳過 {n_bin} 支）、命中 {n_hit}")
    return 1 if n_hit else 0


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


class TestResolveSecretsDir(unittest.TestCase):
    """三級口徑（019 U4 遷移後補：落點遷出 repo 後本層曾一律 skip＝結構性失守、L-174）。"""

    def _root(self, env_body=None):
        import tempfile
        d = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, d, True)
        if env_body is not None:
            with open(os.path.join(d, ".env"), "w", encoding="utf-8") as fh:
                fh.write(env_body)
        return d

    def test_env_var_wins_over_dotenv(self):
        root = self._root("SECRETS_DIR=/tmp/from-dotenv\n")
        sdir, err = resolve_secrets_dir(root, {"SECRETS_DIR": "/tmp/from-envvar"})
        self.assertIsNone(err)
        self.assertEqual(sdir, "/tmp/from-envvar")

    def test_empty_env_var_rejected_loudly(self):
        """★空字串邊界（019 U4 quality）：`SECRETS_DIR` 匯出為空時，compose 的
        `${SECRETS_DIR:-./deploy/secrets}` 直接吃預設值回退 repo 內舊落點、**不讀 .env**；
        本層若把它當未設而續讀 `.env`，即「本層掃新落點、compose 掛舊落點」的靜默分裂
        （修前實證：同一個空字串環境下 preflight 與 guard 皆 rc=0 全綠、compose config
        十條目卻全指 repo 內 deploy/secrets，而該處遷移後零 .txt）。必須吵鬧失敗。"""
        root = self._root("SECRETS_DIR=/tmp/from-dotenv\n")
        sdir, err = resolve_secrets_dir(root, {"SECRETS_DIR": ""})
        self.assertIsNone(sdir)          # ★不得靜默擇一邊（回退或讀 .env 皆是假綠）
        self.assertIn("空字串", err)

    def test_dotenv_used_when_env_var_absent(self):
        root = self._root("# 註解\nSECRETS_DIR=/tmp/rev4-secrets\nOTHER=1\n")
        sdir, err = resolve_secrets_dir(root, {})
        self.assertIsNone(err)
        self.assertEqual(sdir, "/tmp/rev4-secrets")

    def test_dotenv_last_occurrence_wins(self):
        root = self._root("SECRETS_DIR=/tmp/first\nSECRETS_DIR=/tmp/last\n")
        self.assertEqual(resolve_secrets_dir(root, {})[0], "/tmp/last")

    def test_compose_accepted_line_forms_all_recognised(self):
        """★寬進窄出（019 U4）：compose 的 .env 解析器接受的行形——export 前綴／行首縮排／
        等號兩側空白／UTF-8 BOM／CRLF 行尾／值尾空白——本層必須全部認得。行首錨定
        `SECRETS_DIR=` 的窄樣式對前四形**靜默回退** repo 內舊落點（修前實測四形皆回
        root/deploy/secrets 且 err 為 None）→ pre-commit 掃到空目錄、印 skip 且 rc=0，
        裸值格結構性失守而全綠（L-174 經另一條路復發）。
        compose v5.3.1 實測：六形全部解析為新落點。"""
        for label, body in (("export 前綴", "export SECRETS_DIR=/tmp/rev4-new\n"),
                            ("行首縮排", "  SECRETS_DIR=/tmp/rev4-new\n"),
                            ("等號前後空白", "SECRETS_DIR = /tmp/rev4-new\n"),
                            ("UTF-8 BOM", "﻿SECRETS_DIR=/tmp/rev4-new\n"),
                            ("CRLF 行尾", "SECRETS_DIR=/tmp/rev4-new\r\n"),
                            ("值尾空白", "SECRETS_DIR=/tmp/rev4-new   \n")):
            root = self._root(body)
            sdir, err = resolve_secrets_dir(root, {})
            self.assertIsNone(err, label)
            self.assertEqual(sdir, "/tmp/rev4-new", label)

    def test_last_occurrence_wins_across_line_forms(self):
        """後者勝須跨行形成立：舊值裸行＋新值 export 行 → 必取新值。窄樣式修前取舊值、
        compose 取新值，兩邊 rc 皆 0 零錯誤＝契約 P5.1 違反後果欄的「compose 讀新落點、
        腳本查舊落點」。"""
        root = self._root("SECRETS_DIR=/tmp/old\nexport SECRETS_DIR=/tmp/new\n")
        self.assertEqual(resolve_secrets_dir(root, {})[0], "/tmp/new")

    def test_lookalike_key_not_matched(self):
        """寬樣式不得寬到吃掉別的鍵（compose 亦不會把它當 SECRETS_DIR）。"""
        root = self._root("EXTRA_SECRETS_DIR=/tmp/nope\n")
        sdir, err = resolve_secrets_dir(root, {})
        self.assertIsNone(err)
        self.assertEqual(sdir, os.path.join(root, DEFAULT_SECRETS_DIR))

    def test_wide_form_illegal_value_still_rejected_loudly(self):
        """★寬進**窄出**：行形放寬 ≠ 值放寬——寬行形下的相對路徑／元字元／空值仍吵鬧失敗。"""
        for body in ("export SECRETS_DIR=deploy/secrets\n",
                     "  SECRETS_DIR=/tmp/$(id)\n",
                     "SECRETS_DIR = \n"):
            root = self._root(body)
            sdir, err = resolve_secrets_dir(root, {})
            self.assertIsNone(sdir, body)
            self.assertIsNotNone(err, body)

    def test_fallback_when_no_env_var_no_dotenv(self):
        root = self._root()
        sdir, err = resolve_secrets_dir(root, {})
        self.assertIsNone(err)
        self.assertEqual(sdir, os.path.join(root, DEFAULT_SECRETS_DIR))

    def test_dotenv_relative_path_rejected_loudly(self):
        root = self._root("SECRETS_DIR=deploy/secrets\n")
        sdir, err = resolve_secrets_dir(root, {})
        self.assertIsNone(sdir)          # ★不得靜默回退（回退＝掃錯目錄的假綠）
        self.assertIn("絕對路徑", err)

    def test_dotenv_shell_metachar_rejected_loudly(self):
        for body in ("SECRETS_DIR=/tmp/$(id)\n", "SECRETS_DIR=/tmp/a b\n", "SECRETS_DIR=\n"):
            root = self._root(body)
            sdir, err = resolve_secrets_dir(root, {})
            self.assertIsNone(sdir)
            self.assertIsNotNone(err)

    def test_relative_env_var_resolved_against_root(self):
        root = self._root()
        self.assertEqual(resolve_secrets_dir(root, {"SECRETS_DIR": "rel/dir"})[0],
                         os.path.join(root, "rel", "dir"))


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
        """放寬型突變（eligible 恆真）→ EDGE_SKIP 字面邊界綠樣本（7 字元）誤報、self-test 必紅。"""
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "eligible", lambda _v: True), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest())
        self.assertIn("下界邊界綠樣本誤報", buf.getvalue())

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


class TestFullTree(unittest.TestCase):
    """B-118 全樹盤點模式（check --full-tree）：staged 增量模式對「已存在於 tracked 檔的
    機密現值」結構性失明（019 U6 實證、L-190）——本模式一次性掃 git ls-files 全 tracked 檔。"""

    def _fixture(self, d, body_bytes, fname="doc.md"):
        """temp repo＋落點：tracked 檔以 bytes 寫入並 commit（非 staged 新增行）。"""
        repo = os.path.join(d, "repo")
        sec = os.path.join(d, "sec")
        os.makedirs(repo)
        os.makedirs(sec)
        _init_repo(repo)
        v = _fixture_value()
        with open(os.path.join(sec, "fake_key.txt"), "w", encoding="utf-8") as fh:
            fh.write(v)
        with open(os.path.join(repo, fname), "wb") as fh:
            fh.write(body_bytes)
        _git(repo, "add", fname)
        _git(repo, "commit", "-qm", "add")
        return repo, sec, v

    def _run(self, fn, repo, secdir):
        import io, contextlib
        from unittest import mock
        mod = sys.modules[__name__]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(mod, "ROOT", repo), \
                mock.patch.dict(os.environ, {"SECRETS_DIR": secdir}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = fn()
        return rc, out.getvalue() + err.getvalue()

    def test_full_tree_hits_committed_value_names_file_line_never_value(self):
        """①命中印「檔:行｜名」、值零外洩（對輸出全文斷言不含假值字面）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            body = "說明一\n說明二\nurl={} 之類\n"
            repo, sec, v = self._fixture(d, body.format("PLACEHOLDER").replace(
                "PLACEHOLDER", _fixture_value()).encode("utf-8"))
            rc, text = self._run(cmd_full_tree, repo, sec)
            self.assertEqual(rc, 1)
            self.assertIn("doc.md:3｜fake_key", text)
            self.assertNotIn(v, text)   # ★值本身絕不輸出（連遮蔽形都不印）

    def test_staged_mode_blind_to_committed_value_reproduces_b118(self):
        """②同 fixture 走 staged 模式（該行已 commit、非新增）不報＝結構性失明復現。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo, sec, v = self._fixture(
                d, ("x=" + _fixture_value() + "\n").encode("utf-8"))
            rc, _ = self._run(cmd_check, repo, sec)
            self.assertEqual(rc, 0)     # 恰證 B-118：既存明文永不觸發增量模式
            rc, text = self._run(cmd_full_tree, repo, sec)
            self.assertEqual(rc, 1)     # 同一狀態全樹模式必攔
            self.assertIn("doc.md:1｜fake_key", text)

    def test_full_tree_clean_repo_exit_zero(self):
        """③零命中 exit 0。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo, sec, _v = self._fixture(d, "乾淨內容\n沒有機密\n".encode("utf-8"))
            rc, text = self._run(cmd_full_tree, repo, sec)
            self.assertEqual(rc, 0)
            self.assertNotIn("✗", text)

    def test_full_tree_skips_binary_file(self):
        """④binary 檔（含 NUL byte）跳過不炸——即使其位元組串含機密值也不掃（無文字面）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            body = b"\x00\x01\x02" + _fixture_value().encode("utf-8") + b"\x00"
            repo, sec, _v = self._fixture(d, body, fname="blob.bin")
            rc, text = self._run(cmd_full_tree, repo, sec)
            self.assertEqual(rc, 0)
            self.assertNotIn("✗", text)

    def test_full_tree_crlf_line_numbers_correct(self):
        """CRLF 行尾不影響行號：以 \\n 切行、\\r 不另計行。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            body = ("甲\r\n乙\r\nk=" + _fixture_value() + "\r\n").encode("utf-8")
            repo, sec, _v = self._fixture(d, body)
            rc, text = self._run(cmd_full_tree, repo, sec)
            self.assertEqual(rc, 1)
            self.assertIn("doc.md:3｜fake_key", text)

    def test_full_tree_gitlink_entry_skipped_without_warn(self):
        """gitlink（mode 160000＝submodule pin）於外層無 blob 內容——不掃也不 WARN
        （本 repo 兩 submodule 每跑必列＝結構性噪音、且「不視同乾淨」語意誤導）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo, sec, _v = self._fixture(d, "乾淨\n".encode("utf-8"))
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                                  capture_output=True, encoding="utf-8").stdout.strip()
            _git(repo, "update-index", "--add",
                 "--cacheinfo", f"160000,{head},subrepo")
            self.assertNotIn("subrepo", tracked_files(repo))
            rc, text = self._run(cmd_full_tree, repo, sec)
            self.assertEqual(rc, 0)
            self.assertNotIn("WARN", text)

    def test_full_tree_selftest_green_on_healthy_pipeline(self):
        self.assertTrue(run_selftest_full_tree())

    def test_full_tree_selftest_catches_dead_matcher(self):
        """比對邏輯死掉（恆空）→ self-test 必紅（防恆綠、同 check 慣例）。"""
        from unittest import mock
        mod = sys.modules[__name__]
        import io, contextlib
        buf = io.StringIO()
        with mock.patch.object(mod, "scan_tree_lines", lambda *_a: []), \
                contextlib.redirect_stderr(buf):
            self.assertFalse(run_selftest_full_tree())
        self.assertIn("紅樣本未攔", buf.getvalue())

    def test_full_tree_selftest_never_prints_sample_values(self):
        import io, contextlib
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run_selftest_full_tree()
        self.assertNotIn("RV4" + "TREE", out.getvalue() + err.getvalue())


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

    def test_check_full_tree_flag_routes_to_full_tree(self):
        from unittest import mock
        mod = sys.modules[__name__]
        with mock.patch.object(mod, "cmd_full_tree", lambda: 42):
            self.assertEqual(self._main(["check", "--full-tree"]), 42)

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
        if argv[2:] == ["--full-tree"]:
            return cmd_full_tree()
        if argv[2:]:
            return usage(f"check：僅收 --full-tree 單一旗標（見 {' '.join(argv[2:])}）")
        return cmd_check()
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
