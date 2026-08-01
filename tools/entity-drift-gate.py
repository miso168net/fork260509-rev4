#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/entity-drift-gate.py — entity×schema 快照漂移閘（python 標準庫、單檔、自帶測試）

子命令：
  check   entity 漂移比對（B-110 階段 0；零 docker、秒級、掛 pre-commit）：
          左源＝docs/ops/reference-src/schema-snapshot.json 的 columns 節（已 commit
          快照）、右源＝rust-api/entity/src/*.rs（排除 lib.rs）——雙向表／欄完整性
          ＋型別（TYPE_MAP）＋可空性（Option vs nullable）比對
  test    跑自帶測試（unittest、離線可跑）

退出碼（照 tools/schema-gate.py 語意）：零漂移 0；有漂移 1＋逐項指名；環境／結構異常
（快照缺席或 JSON 壞、columns 節空或缺、entity 目錄缺席、解析 0 表、豁免後比對面為空、
未知 rust 型別）2＋補救提示；用法錯誤 64（EX_USAGE、usage 走 stderr）。

skip-list＝casbin_rule（ADR 0015：該表委派 casbin adapter 建基底、不入我方 entity
治理比對）——雙向豁免、check 輸出一行 SKIP 註記指名 ADR 0015。

明確不驗三項（各有去處）：欄序（ADR 0021 歸 schema-gate gate2）、default（entity 面
無此資訊）、index/constraint（schema-gate gate1 轄區）。

check 入口無條件合成 self-test（照 tools/wire-schema.py check_self_test 模式）：合成
健康 snapshot×entity 對必綠＋注入假漂移（欄缺席／型別不符／可空性三型）必紅；
self-test 失敗＝rc 2 指名比對邏輯壞、不讀任何真檔。未知型別絕不靜默跳過＝rc 2
fail-loud（原型的靜默跳過是已知缺陷、不承襲）。
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
import unittest.mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 左源＝已 commit 的 schema 快照（docs-sync refresh 產物；columns 節＝list[dict]、
# 鍵＝table/column/ordinal/type/nullable/default）。
SNAPSHOT_REL = os.path.join("docs", "ops", "reference-src", "schema-snapshot.json")
# 右源＝entity worktree（lib.rs 為模組匯出、非 entity、排除）。
ENTITY_DIR_REL = os.path.join("rust-api", "entity", "src")

# skip-list（ADR 0015）：casbin_rule 委派 adapter 建基底、雙向豁免。
SKIP_TABLES = ("casbin_rule",)

# rust 基礎型別 → 快照正規化型別容許集（快照型別先去長度修飾再查）。
# ★不在表內的型別＝GateError（rc 2 fail-loud）、絕不靜默跳過。
TYPE_MAP = {
    "i64": ("bigint",),
    "i32": ("integer",),
    "i16": ("smallint",),
    "String": ("character varying", "text"),
    "bool": ("boolean",),
    "DateTimeWithTimeZone": ("timestamp with time zone",),
    "Json": ("jsonb", "json"),
    "IpNetwork": ("inet",),
    "Decimal": ("numeric",),
    "Vec<u8>": ("bytea",),
}

# entity 源碼解析（DeriveEntityModel 慣例形）：表名屬性／Model 結構體／欄名改寫屬性／欄行。
RE_TABLE_NAME = re.compile(r'#\[sea_orm\(table_name\s*=\s*"([^"]+)"')
RE_MODEL_BODY = re.compile(r"pub struct Model \{(.*?)\n\}", re.S)
RE_COLUMN_NAME_ATTR = re.compile(r'#\[sea_orm\([^)]*column_name\s*=\s*"([^"]+)"')
RE_FIELD = re.compile(r"pub (?:r#)?(\w+):\s*(.+?),?\s*$")
# 快照型別長度修飾（character varying(45)／numeric(10,2)）→ 去尾正規化。
RE_LEN_SUFFIX = re.compile(r"\(\d+(?:,\s*\d+)?\)$")


class GateError(Exception):
    """結構／環境異常（未知型別、豁免後比對面為空等）——走 rc 2、絕不靜默。"""


def normalize_db_type(db_type):
    """快照型別正規化：去長度修飾（character varying(45)→character varying）。"""
    return RE_LEN_SUFFIX.sub("", db_type.strip()).strip()


def parse_entity(source):
    """entity 源碼 → (表名, [(DB 欄名, 基礎型別, 是否 Option), …])；缺 table_name 或
    Model 結構體＝None。欄行前 #[sea_orm(column_name = "…")] 屬性值＝DB 欄名（支援
    改名情境）；其他 #[sea_orm(…)] 屬性行（primary_key 等）忽略。"""
    tm = RE_TABLE_NAME.search(source)
    body = RE_MODEL_BODY.search(source)
    if not tm or not body:
        return None
    cols = []
    pending_name = None       # column_name 屬性值暫存、用於下一欄行
    for raw in body.group(1).splitlines():
        line = raw.strip()
        if line.startswith("#["):
            m = RE_COLUMN_NAME_ATTR.match(line)
            if m:
                pending_name = m.group(1)
            continue          # 其他 sea_orm 屬性行（primary_key 等）＝忽略、不清暫存
        fm = RE_FIELD.match(line)
        if not fm:
            continue
        name = pending_name if pending_name is not None else fm.group(1)
        pending_name = None
        ty = fm.group(2).strip()
        is_opt = ty.startswith("Option<") and ty.endswith(">")
        base = ty[len("Option<"):-1].strip() if is_opt else ty
        cols.append((name, base, is_opt))
    return tm.group(1), cols


def compare(snapshot_columns, entities):
    """純比對（檔案 IO 只在邊界、本函式吃合成資料即可證紅綠）：
    snapshot_columns＝快照 columns 節（list[dict]）、entities＝{表名: 欄列表}。
    回 findings 字串清單（零漂移＝空清單）。SKIP_TABLES 雙向豁免；未知 rust 型別
    ／豁免後比對面為空＝raise GateError（rc 2 fail-loud）。"""
    snap = {}
    for c in snapshot_columns:
        t = c.get("table")
        if t in SKIP_TABLES:
            continue
        snap.setdefault(t, {})[c.get("column")] = c
    ents = {t: cols for t, cols in entities.items() if t not in SKIP_TABLES}
    if not snap or not ents:
        raise GateError("豁免後比對面為空（快照或 entity 側零表）——空集不得靜默判綠；"
                        "確認快照與 rust-api/entity/src 內容後重跑")
    # ★未知型別先於一切配對 fail-loud（含快照側缺席之欄——絕不降級為 DRIFT 靜默混過）。
    for t, cols in sorted(ents.items()):
        for name, base, _opt in cols:
            if base not in TYPE_MAP:
                raise GateError(f"未知 rust 型別「{base}」（{t}.{name}）不在 TYPE_MAP"
                                "——fail-loud、絕不靜默跳過；新型別先補 TYPE_MAP 再回頭")
    findings = []
    # a) entity 表不在快照／b) 快照表無對應 entity（反向完整性）。
    for t in sorted(set(ents) - set(snap)):
        findings.append(f"表 {t}｜entity 有、快照無")
    for t in sorted(set(snap) - set(ents)):
        findings.append(f"表 {t}｜快照有、entity 無")
    # 共同表逐欄：c) d) 完整性、e) 型別、f) 可空性。
    for t in sorted(set(snap) & set(ents)):
        ent_cols = {name: (base, opt) for name, base, opt in ents[t]}
        for name in sorted(set(ent_cols) - set(snap[t])):
            findings.append(f"欄 {t}.{name}｜entity 有、快照無")
        for name in sorted(set(snap[t]) - set(ent_cols)):
            findings.append(f"欄 {t}.{name}｜快照有、entity 無")
        for name in sorted(set(ent_cols) & set(snap[t])):
            base, opt = ent_cols[name]
            norm = normalize_db_type(str(snap[t][name].get("type")))
            if norm not in TYPE_MAP[base]:
                findings.append(f"型別 {t}.{name}｜entity {base}（期望 "
                                f"{'／'.join(TYPE_MAP[base])}）、快照 {norm}")
            nullable = bool(snap[t][name].get("nullable"))
            if opt != nullable:
                findings.append(f"可空性 {t}.{name}｜entity Option＝{opt}、"
                                f"快照 nullable＝{nullable}")
    return findings


def check_self_test():
    """check 入口無條件合成 self-test（照 tools/wire-schema.py check_self_test 模式）：
    健康對必綠＋注入欄缺席／型別不符／可空性三型假漂移必紅——失敗即比對邏輯壞、
    不讀任何真檔（防恆綠）。"""
    snap = [
        {"table": "t_ok", "column": "id", "ordinal": 1, "type": "bigint",
         "nullable": False, "default": None},
        {"table": "t_ok", "column": "name", "ordinal": 2,
         "type": "character varying(64)", "nullable": True, "default": None},
    ]
    healthy = {"t_ok": [("id", "i64", False), ("name", "String", True)]}
    if compare(snap, healthy) != []:
        raise AssertionError("健康合成對被誤判為漂移")
    if not compare(snap, {"t_ok": [("id", "i64", False)]}):
        raise AssertionError("欄缺席假漂移未被攔")
    bad_type = {"t_ok": [("id", "i32", False), ("name", "String", True)]}
    if not any("型別" in f for f in compare(snap, bad_type)):
        raise AssertionError("型別不符假漂移未被攔")
    bad_null = {"t_ok": [("id", "i64", True), ("name", "String", True)]}
    if not any("可空" in f for f in compare(snap, bad_null)):
        raise AssertionError("可空性假漂移未被攔")


def load_entities(ent_dir):
    """entity 目錄 → {表名: 欄列表}。lib.rs 排除；.rs 解析失敗（缺 table_name／Model）
    ＝GateError fail-loud（靜默跳過會讓該表漂移報成「快照有、entity 無」誤導補救）。"""
    entities = {}
    for fn in sorted(os.listdir(ent_dir)):
        if not fn.endswith(".rs") or fn == "lib.rs":
            continue
        with open(os.path.join(ent_dir, fn), encoding="utf-8") as fh:
            parsed = parse_entity(fh.read())
        if parsed is None:
            raise GateError(f"{fn} 解析失敗（缺 table_name 屬性或 pub struct Model）"
                            "——非 entity 檔請勿放 rust-api/entity/src")
        if parsed[0] in entities:
            raise GateError(f"{fn} 宣告的 table_name「{parsed[0]}」與另一 entity 檔重複"
                            "——重複宣告會靜默後蓋前（整表欄集被丟棄）；先併檔再回頭")
        entities[parsed[0]] = parsed[1]
    return entities


def cmd_check(root=REPO_ROOT):
    """check 子命令：self-test → 載快照 → 解析 entity → 比對 → 逐項指名。"""
    # ① 無條件合成 self-test（防恆綠；失敗＝不讀任何真檔）。兩種失敗模式都收：
    # AssertionError（假漂移沒攔到）＋GateError（TYPE_MAP／SKIP_TABLES 被改壞）——
    # 後者若逃逸＝rc 1 traceback、與「有漂移」語意相撞。
    try:
        check_self_test()
    except (AssertionError, GateError) as ex:
        print(f"[check] ✗ self-test 失敗（比對邏輯壞）：{ex}", file=sys.stderr)
        return 2
    # ② 左源：快照載入（缺席／JSON 壞／columns 空或缺＝rc 2＋補救提示）。
    snap_path = os.path.join(root, SNAPSHOT_REL)
    try:
        with open(snap_path, encoding="utf-8") as fh:
            snap = json.load(fh)
    except FileNotFoundError:
        print(f"[check] ✗ 快照檔缺席（{SNAPSHOT_REL}）——補救：起 stack 後跑 "
              "python3 tools/docs-sync.py refresh 重抽快照", file=sys.stderr)
        return 2
    except json.JSONDecodeError as ex:
        print(f"[check] ✗ 快照檔非合法 JSON（{ex}）——補救：python3 tools/docs-sync.py "
              "refresh 重抽快照", file=sys.stderr)
        return 2
    columns = snap.get("columns") if isinstance(snap, dict) else None
    if not isinstance(columns, list) or not columns:
        print("[check] ✗ 快照 columns 節空或缺——快照結構異常，補救：python3 "
              "tools/docs-sync.py refresh 重抽快照", file=sys.stderr)
        return 2
    # ③ 右源：entity 目錄（缺席＝worktree 未建）與解析。
    ent_dir = os.path.join(root, ENTITY_DIR_REL)
    if not os.path.isdir(ent_dir):
        print(f"[check] ✗ {ENTITY_DIR_REL} 目錄缺席（rust-api worktree 未建？）——"
              "補救：bash tools/bootstrap.sh", file=sys.stderr)
        return 2
    try:
        entities = load_entities(ent_dir)
    except GateError as ex:
        print(f"[check] ✗ {ex}", file=sys.stderr)
        return 2
    if not entities:
        print(f"[check] ✗ 解析出 0 個 entity 表（{ENTITY_DIR_REL} 無有效 entity 檔）"
              "——空集不得靜默判綠；worktree 內容存疑先跑 bash tools/bootstrap.sh 體檢",
              file=sys.stderr)
        return 2
    # ④ 比對（純函式；未知型別／豁免後比對面為空＝GateError→rc 2）。
    snap_tables = sorted({c.get("table") for c in columns})
    skipped = sorted((set(snap_tables) | set(entities)) & set(SKIP_TABLES))
    try:
        findings = compare(columns, entities)
    except GateError as ex:
        print(f"[check] ✗ {ex}", file=sys.stderr)
        return 2
    for t in skipped:
        print(f"[check] SKIP {t}（ADR 0015：委派 adapter 建基底、不入 entity 治理比對）")
    if findings:
        print(f"[check] ✗ {len(findings)} 條 entity×快照 漂移：", file=sys.stderr)
        for f in findings:
            print(f"    DRIFT {f}", file=sys.stderr)
        print("  補救：entity 面錯→改 rust-api/entity/src；快照過期（migration 已前進）"
              "→起 stack 跑 python3 tools/docs-sync.py refresh 重抽後審 diff。",
              file=sys.stderr)
        return 1
    n_compared = len(set(snap_tables) - set(SKIP_TABLES))
    print(f"[check] ✓ entity×快照 零漂移（快照 {len(snap_tables)} 表、entity "
          f"{len(entities)} 表、豁免 {'、'.join(skipped) if skipped else '無'}、"
          f"實比對 {n_compared} 表、0 findings）")
    return 0


# ---------------------------------------------------------------------------
# 自帶測試（unittest、離線可跑——不觸 docker、不讀真 repo 檔）
# ---------------------------------------------------------------------------

# 合成健康對（多數案共用基底；表名取合成名、避免與真表混淆）。
FIX_SNAP = [
    {"table": "t_user", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": None},
    {"table": "t_user", "column": "name", "ordinal": 2,
     "type": "character varying(64)", "nullable": False, "default": None},
    {"table": "t_user", "column": "memo", "ordinal": 3, "type": "text",
     "nullable": True, "default": None},
    {"table": "t_log", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": None},
    {"table": "t_log", "column": "meta", "ordinal": 2, "type": "jsonb",
     "nullable": True, "default": None},
    {"table": "t_log", "column": "ip", "ordinal": 3, "type": "inet",
     "nullable": False, "default": None},
]
FIX_ENTS = {
    "t_user": [("id", "i64", False), ("name", "String", False), ("memo", "String", True)],
    "t_log": [("id", "i64", False), ("meta", "Json", True), ("ip", "IpNetwork", False)],
}

ENTITY_SRC = '''//! 合成 entity（測試用）。
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Eq)]
#[sea_orm(table_name = "t_user")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i64,
    #[sea_orm(column_name = "order")]
    pub order_field: Option<i32>,
    pub name: String,
    pub memo: Option<String>,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {}

impl ActiveModelBehavior for ActiveModel {}
'''


class TestNormalize(unittest.TestCase):
    """快照型別正規化：長度修飾去尾、無修飾原樣。"""

    def test_strips_length_modifier(self):
        self.assertEqual(normalize_db_type("character varying(45)"), "character varying")
        self.assertEqual(normalize_db_type("numeric(10,2)"), "numeric")

    def test_plain_types_unchanged(self):
        self.assertEqual(normalize_db_type("bigint"), "bigint")
        self.assertEqual(normalize_db_type("timestamp with time zone"),
                         "timestamp with time zone")


class TestParser(unittest.TestCase):
    """entity 源碼解析：表名／欄行／column_name 改寫／Option 剝殼／屬性忽略。"""

    def test_parses_table_name_and_fields(self):
        table, cols = parse_entity(ENTITY_SRC)
        self.assertEqual(table, "t_user")
        self.assertEqual(cols[0], ("id", "i64", False))
        self.assertEqual(cols[2], ("name", "String", False))

    def test_column_name_attr_overrides_field_name(self):
        """改名情境：#[sea_orm(column_name = "order")] 之欄 DB 名＝屬性值、非 rust 欄名。"""
        _, cols = parse_entity(ENTITY_SRC)
        self.assertIn(("order", "i32", True), cols)
        self.assertNotIn("order_field", [c[0] for c in cols])

    def test_option_unwrap(self):
        _, cols = parse_entity(ENTITY_SRC)
        self.assertEqual(cols[3], ("memo", "String", True))

    def test_primary_key_attr_ignored(self):
        """primary_key 等其他 sea_orm 屬性行不產欄、不影響下一欄名。"""
        _, cols = parse_entity(ENTITY_SRC)
        self.assertEqual(len(cols), 4)

    def test_missing_table_name_returns_none(self):
        self.assertIsNone(parse_entity("//! lib 型檔案\npub mod t_user;\n"))

    def test_raw_identifier_field_strips_prefix(self):
        """r# 原始識別字欄（rust 關鍵字撞名慣例形）：DB 欄名＝去 r# 前綴之名——
        RE_FIELD 的 (?:r#)? 分支被拆時此案即紅。"""
        src = ('#[sea_orm(table_name = "t_x")]\n'
               "pub struct Model {\n"
               "    pub r#type: String,\n"
               "}\n")
        table, cols = parse_entity(src)
        self.assertEqual(table, "t_x")
        self.assertEqual(cols, [("type", "String", False)])


class TestCompareGreen(unittest.TestCase):
    """健康對零 findings；String／Json 多容許型別皆綠；長度修飾正規化後綠。"""

    def test_healthy_pair_zero_findings(self):
        self.assertEqual(compare(FIX_SNAP, dict(FIX_ENTS)), [])

    def test_string_matches_both_varchar_and_text(self):
        snap = [dict(FIX_SNAP[1]), dict(FIX_SNAP[2])]
        ents = {"t_user": [("name", "String", False), ("memo", "String", True)]}
        self.assertEqual(compare(snap, ents), [])


class TestCompareDrifts(unittest.TestCase):
    """六型比對逐一紅證（a 表多／b 表缺／c 欄多／d 欄缺／e 型別／f 可空性）。"""

    def test_a_entity_table_not_in_snapshot(self):
        ents = dict(FIX_ENTS, t_new=[("id", "i64", False)])
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("t_new", fs[0])
        self.assertIn("快照無", fs[0])

    def test_b_snapshot_table_without_entity(self):
        ents = {"t_user": list(FIX_ENTS["t_user"])}   # 少 t_log
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("t_log", fs[0])
        self.assertIn("entity 無", fs[0])

    def test_c_entity_column_not_in_snapshot(self):
        ents = dict(FIX_ENTS)
        ents["t_user"] = FIX_ENTS["t_user"] + [("extra", "i64", True)]
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("t_user.extra", fs[0])
        self.assertIn("快照無", fs[0])

    def test_d_snapshot_column_without_entity(self):
        ents = dict(FIX_ENTS)
        ents["t_user"] = FIX_ENTS["t_user"][:2]       # 少 memo
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("t_user.memo", fs[0])
        self.assertIn("entity 無", fs[0])

    def test_e_type_mismatch(self):
        ents = dict(FIX_ENTS)
        ents["t_user"] = [("id", "i32", False)] + FIX_ENTS["t_user"][1:]
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("型別", fs[0])
        self.assertIn("t_user.id", fs[0])

    def test_f_nullability_mismatch(self):
        ents = dict(FIX_ENTS)
        ents["t_user"] = [("id", "i64", True)] + FIX_ENTS["t_user"][1:]
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("可空", fs[0])
        self.assertIn("t_user.id", fs[0])

    def test_f_nullability_mismatch_reverse(self):
        """f 反向（entity 非 Option、快照 nullable＝True）——後果較重的一側：sea-orm
        以非 Option 欄反序列化真 NULL 會炸。只測單向會讓「opt and not nullable」
        弱化編輯全綠存活、此案釘住雙向判定。"""
        ents = dict(FIX_ENTS)
        ents["t_user"] = FIX_ENTS["t_user"][:2] + [("memo", "String", False)]
        fs = compare(FIX_SNAP, ents)
        self.assertEqual(len(fs), 1, msg=str(fs))
        self.assertIn("可空", fs[0])
        self.assertIn("t_user.memo", fs[0])


class TestUnknownTypeFailLoud(unittest.TestCase):
    """未知 rust 型別＝GateError（絕不靜默跳過——原型已知缺陷、不承襲）。"""

    def test_unknown_type_raises(self):
        ents = dict(FIX_ENTS)
        ents["t_user"] = [("id", "f64", False)] + FIX_ENTS["t_user"][1:]
        with self.assertRaises(GateError) as cm:
            compare(FIX_SNAP, ents)
        self.assertIn("f64", str(cm.exception))
        self.assertIn("TYPE_MAP", str(cm.exception))

    def test_unknown_type_raises_even_when_column_not_in_snapshot(self):
        """未知型別欄即使快照側缺席（同時是漂移 c）仍先 fail-loud、不降級為 DRIFT。"""
        ents = dict(FIX_ENTS)
        ents["t_user"] = FIX_ENTS["t_user"] + [("odd", "f32", True)]
        with self.assertRaises(GateError):
            compare(FIX_SNAP, ents)


class TestSkipList(unittest.TestCase):
    """casbin_rule 雙向豁免（ADR 0015）＋豁免後比對面為空＝GateError。"""

    CASBIN_SNAP = [{"table": "casbin_rule", "column": "id", "ordinal": 1,
                    "type": "bigint", "nullable": False, "default": None}]

    def test_snapshot_side_casbin_exempted(self):
        self.assertEqual(compare(FIX_SNAP + self.CASBIN_SNAP, dict(FIX_ENTS)), [])

    def test_entity_side_casbin_exempted(self):
        ents = dict(FIX_ENTS, casbin_rule=[("id", "i64", False)])
        self.assertEqual(compare(FIX_SNAP, ents), [])

    def test_all_exempted_surface_empty_raises(self):
        with self.assertRaises(GateError) as cm:
            compare(self.CASBIN_SNAP, {"casbin_rule": [("id", "i64", False)]})
        self.assertIn("比對面為空", str(cm.exception))

    def test_snapshot_side_empty_after_exemption_raises(self):
        """★單側空即 GateError（快照側）：只測雙側空會讓空集判定 or 改 and 的
        弱化編輯全綠存活——單側空必然全表漂移、屬結構異常非漂移。"""
        with self.assertRaises(GateError):
            compare(self.CASBIN_SNAP, dict(FIX_ENTS))

    def test_entity_side_empty_after_exemption_raises(self):
        """★單側空即 GateError（entity 側）——同上、另一側向。"""
        with self.assertRaises(GateError):
            compare(FIX_SNAP, {"casbin_rule": [("id", "i64", False)]})


class TestGovernanceConstantsPinned(unittest.TestCase):
    """治理常數字面釘死（慣例＝schema-gate TestWhitelist）：SKIP_TABLES 與 TYPE_MAP
    是豁免／容差名冊，放寬一行＝閘靜默縮水（漂移永久失明）——只迭代常數的斷言
    是套套邏輯，字面釘死使單邊改動（擴充豁免、放寬容差）當場紅。"""

    def test_skip_tables_pinned(self):
        self.assertEqual(SKIP_TABLES, ("casbin_rule",))

    def test_type_map_pinned(self):
        self.assertEqual(TYPE_MAP, {
            "i64": ("bigint",),
            "i32": ("integer",),
            "i16": ("smallint",),
            "String": ("character varying", "text"),
            "bool": ("boolean",),
            "DateTimeWithTimeZone": ("timestamp with time zone",),
            "Json": ("jsonb", "json"),
            "IpNetwork": ("inet",),
            "Decimal": ("numeric",),
            "Vec<u8>": ("bytea",),
        })


class TestSelfTest(unittest.TestCase):
    """入口合成 self-test：健康邏輯不 raise；比對邏輯壞→check rc 2、不讀任何真檔。"""

    def test_self_test_passes_on_healthy_logic(self):
        check_self_test()

    def test_broken_compare_rc2_without_reading_files(self):
        err = io.StringIO()
        with unittest.mock.patch.object(
                sys.modules[__name__], "compare", lambda a, b: []):
            with contextlib.redirect_stderr(err):
                rc = cmd_check(root="/nonexistent/entity-drift-gate-selftest")
        self.assertEqual(rc, 2)
        self.assertIn("self-test 失敗", err.getvalue())
        self.assertIn("比對邏輯壞", err.getvalue())

    def test_broken_type_map_gateerror_rc2_without_reading_files(self):
        """守備面另一半：TYPE_MAP 被改壞（拔 i64 鍵）→ self-test 內 compare 拋
        GateError（非 AssertionError）——仍須 rc 2 指名比對邏輯壞、不讀任何真檔，
        絕不逃逸成 traceback（逃逸＝rc 1、與「有漂移」語意相撞、誤導維運去翻
        entity／migration）。"""
        err = io.StringIO()
        trimmed = {k: v for k, v in TYPE_MAP.items() if k != "i64"}
        with unittest.mock.patch.dict(TYPE_MAP, trimmed, clear=True):
            with contextlib.redirect_stderr(err):
                rc = cmd_check(root="/nonexistent/entity-drift-gate-selftest")
        self.assertEqual(rc, 2)
        self.assertIn("self-test 失敗", err.getvalue())
        self.assertIn("TYPE_MAP", err.getvalue())


def _sandbox_root(d, snapshot=None, entity_files=None, raw_snapshot=None):
    """cmd_check 沙盒：快照＋entity 目錄自建（None＝該側不建）。"""
    if raw_snapshot is not None:
        path = os.path.join(d, SNAPSHOT_REL)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(raw_snapshot)
    elif snapshot is not None:
        path = os.path.join(d, SNAPSHOT_REL)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, ensure_ascii=False)
    if entity_files is not None:
        ent_dir = os.path.join(d, ENTITY_DIR_REL)
        os.makedirs(ent_dir, exist_ok=True)
        for fn, src in entity_files.items():
            with open(os.path.join(ent_dir, fn), "w", encoding="utf-8") as fh:
                fh.write(src)


SANDBOX_ENTITY = ('#[sea_orm(table_name = "t_user")]\n'
                  "pub struct Model {\n"
                  "    pub id: i64,\n"
                  "    pub name: String,\n"
                  "}\n")
SANDBOX_SNAP = {"columns": [
    {"table": "t_user", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": None},
    {"table": "t_user", "column": "name", "ordinal": 2,
     "type": "character varying(64)", "nullable": False, "default": None},
]}


class TestCmdCheck(unittest.TestCase):
    """check 端到端（沙盒 root）：退出碼 0/1/2 三路＋SKIP 註記＋空集 fail-loud。"""

    def test_zero_drift_rc0(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP,
                          entity_files={"t_user.rs": SANDBOX_ENTITY})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cmd_check(root=d), 0)
            self.assertIn("零漂移", out.getvalue())
            self.assertIn("0 findings", out.getvalue())

    def test_drift_rc1_names_each_finding(self):
        snap = {"columns": SANDBOX_SNAP["columns"] + [
            {"table": "t_user", "column": "ghost", "ordinal": 3, "type": "text",
             "nullable": True, "default": None}]}
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=snap,
                          entity_files={"t_user.rs": SANDBOX_ENTITY})
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 1)
            self.assertIn("t_user.ghost", err.getvalue())
            self.assertIn("DRIFT", err.getvalue())

    def test_skip_note_names_adr_0015(self):
        snap = {"columns": SANDBOX_SNAP["columns"] + [
            {"table": "casbin_rule", "column": "id", "ordinal": 1, "type": "bigint",
             "nullable": False, "default": None}]}
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=snap,
                          entity_files={"t_user.rs": SANDBOX_ENTITY})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cmd_check(root=d), 0)
            self.assertIn("SKIP casbin_rule", out.getvalue())
            self.assertIn("ADR 0015", out.getvalue())

    def test_missing_snapshot_rc2_with_remedy(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, entity_files={"t_user.rs": SANDBOX_ENTITY})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("快照檔缺席", err.getvalue())
            self.assertIn("refresh", err.getvalue())

    def test_bad_json_snapshot_rc2(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, raw_snapshot="{壞 json",
                          entity_files={"t_user.rs": SANDBOX_ENTITY})
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cmd_check(root=d), 2)

    def test_empty_columns_rc2(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot={"columns": []},
                          entity_files={"t_user.rs": SANDBOX_ENTITY})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("columns", err.getvalue())

    def test_missing_entity_dir_rc2_hints_bootstrap(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("bash tools/bootstrap.sh", err.getvalue())

    def test_zero_entity_tables_rc2(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP,
                          entity_files={"lib.rs": "pub mod t_user;\n"})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("0 個 entity 表", err.getvalue())

    def test_unparseable_entity_file_rc2(self):
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP,
                          entity_files={"t_user.rs": SANDBOX_ENTITY,
                                        "broken.rs": "pub struct Other {}\n"})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("broken.rs", err.getvalue())

    def test_duplicate_table_name_rc2(self):
        """兩檔宣告同一 table_name＝rc 2 fail-loud——靜默後蓋前會整表欄集丟棄、
        比對面悄悄縮水（全檔僅此一條殘留靜默路徑、本案封死）。"""
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP,
                          entity_files={"t_user.rs": SANDBOX_ENTITY,
                                        "t_user_dup.rs": SANDBOX_ENTITY})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("t_user", err.getvalue())
            self.assertIn("重複", err.getvalue())

    def test_skip_note_entity_side_only_and_compared_count(self):
        """SKIP 註記於 casbin_rule 僅 entity 側命中時同樣列印；零漂移行印實比對表數
        （快照側扣豁免）——兩者原無斷言覆蓋、此案補齊。"""
        casbin_entity = ('#[sea_orm(table_name = "casbin_rule")]\n'
                         "pub struct Model {\n"
                         "    pub id: i64,\n"
                         "}\n")
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP,
                          entity_files={"t_user.rs": SANDBOX_ENTITY,
                                        "casbin_rule.rs": casbin_entity})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cmd_check(root=d), 0)
            self.assertIn("SKIP casbin_rule", out.getvalue())
            self.assertIn("實比對 1 表", out.getvalue())

    def test_unknown_type_on_main_compare_path_rc2(self):
        """主比對路徑未知型別（f64 不在 TYPE_MAP）→ rc 2、stderr 指名 TYPE_MAP——
        釘住 cmd_check 對 compare 的 GateError 攔截：攔截被拆＝未捕捉例外 rc 1
        ＋traceback、與檔頭「漂移 1、異常 2」語意相撞（self-test 路徑已有同級
        守衛、此案補主路徑）。可達性高：TYPE_MAP 未含 Uuid／Date／f64 等常見
        sea-orm 型別、下次加此類欄即走到這條路。"""
        entity_with_f64 = ('#[sea_orm(table_name = "t_user")]\n'
                           "pub struct Model {\n"
                           "    pub id: i64,\n"
                           "    pub name: String,\n"
                           "    pub score: f64,\n"
                           "}\n")
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=SANDBOX_SNAP,
                          entity_files={"t_user.rs": entity_with_f64})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("TYPE_MAP", err.getvalue())
            self.assertIn("f64", err.getvalue())

    def test_all_exempted_surface_empty_rc2(self):
        """豁免後比對面為空（兩側僅剩 casbin_rule）→ rc 2、絕不靜默判綠——
        GateError 攔截的第二來源在退出碼層釘住。"""
        casbin_snap = {"columns": [
            {"table": "casbin_rule", "column": "id", "ordinal": 1, "type": "bigint",
             "nullable": False, "default": None}]}
        casbin_entity = ('#[sea_orm(table_name = "casbin_rule")]\n'
                         "pub struct Model {\n"
                         "    pub id: i64,\n"
                         "}\n")
        with tempfile.TemporaryDirectory() as d:
            _sandbox_root(d, snapshot=casbin_snap,
                          entity_files={"casbin_rule.rs": casbin_entity})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cmd_check(root=d), 2)
            self.assertIn("比對面為空", err.getvalue())


class TestUsage(unittest.TestCase):
    """用法錯誤＝exit 64（EX_USAGE）、usage 走 stderr。"""

    def test_no_args_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["entity-drift-gate.py"]), 64)

    def test_unknown_subcommand_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["entity-drift-gate.py", "bogus"]), 64)

    def test_check_rejects_extra_args_exit64(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["entity-drift-gate.py", "check", "--x"]), 64)


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
    if cmd == "check":
        if argv[2:]:
            return usage(f"check：不收參數（見 {' '.join(argv[2:])}）")
        return cmd_check()
    return usage(f"未知子命令：{cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
