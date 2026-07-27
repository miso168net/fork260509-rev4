#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/docs-sync.py — rev4 文件系統生成器＋lint（python 標準庫、單檔、自帶測試）

子命令：
  generate        重算 docs/generated/ 全部（含 ADR superseded_by 對稱回填）
  check           重算到暫存與現況 diff、不一致 exit 1（= lint L1 本體＋L2 對賬）
  lint            L3～L16（L4/L5/L6 收刀完整性閘：事件存在性／review 分流／arch_impact 雙向；
                  L16 憑證內容掃描：外層 tracked 全量＋pin bump 時 submodule 增量）
  refresh         自實庫撈快照寫 docs/ops/reference-src/（唯一需 docker 的子命令）
  errata <詞>     全 repo 同語意枚舉報告
  test            跑自帶測試（unittest）

token 計數：UTF-8 bytes ÷ 3 保守近似（測試鎖定算法）。
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# 共用基礎
# ---------------------------------------------------------------------------

# repo 相對路徑常數
EVENTS = "docs/ops/events.jsonl"
BOOK = "docs/arc42/ARCHITECTURE.md"
NOTES = "docs/ops/NOTES.md"
BACKLOG = "docs/ops/BACKLOG.md"
STATE = "docs/generated/STATE.md"
ADR_DIR = "docs/arc42/decisions"
GENERATED_DIR = "docs/generated"


def token_count(text):
    """token 保守近似 = UTF-8 bytes ÷ 3（整數除法）。"""
    return len(text.encode("utf-8")) // 3


def _yaml_scalar(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def parse_front_matter(text):
    """解析 md 檔頭 front-matter（YAML 子集：scalar、flow list、行首 key:）。

    回 (meta_dict, body_str)；無 front-matter 回 ({}, 原文)。
    支援：字串 scalar（可帶引號）、flow list [a, b]、空 list []。
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "".join(lines[i + 1:])
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            val = [_yaml_scalar(x) for x in inner.split(",")] if inner else []
        else:
            val = _yaml_scalar(raw)
        meta[key.strip()] = val
    return {}, text  # 沒關閉的 front-matter：視同無


# ---------------------------------------------------------------------------
# lint 基礎設施
# ---------------------------------------------------------------------------

ERROR, WARN = "ERROR", "WARN"


def finding(level, code, where, msg):
    return {"level": level, "code": code, "where": where, "msg": msg}


RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_FEATURE = re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*$")
RE_SHA = re.compile(r"^[0-9a-f]{7,40}$")
RE_SECTION = re.compile(r"^§\d{1,2}$")
RE_ADR_ID = re.compile(r"^\d{4}$")
RE_BID = re.compile(r"^B-\d{3,}$")

EVENT_SCHEMAS = {
    "feature_close": {
        "required": ["type", "feature", "merge", "date", "summary", "pins",
                     "adrs", "arch_impact", "backlog_add", "backlog_done"],
        "optional": ["kind", "spec_supersessions", "notes"],
    },
    "review": {
        "required": ["type", "date", "scope", "report", "findings"],
        "optional": ["notes"],
    },
    "misc": {
        "required": ["type", "date", "summary"],
        # backlog_done：輕量軌收刀（非 NNN- branch、無 feature_close 事件）消化 BACKLOG 條目的
        # 唯一證據通道（L4/L5 對賬同源；user 拍板調規 2026-07-17——維護批首例）。
        "optional": ["notes", "backlog_done"],
    },
}


def _id_list_ok(v, pattern):
    return (isinstance(v, list)
            and all(isinstance(x, str) and pattern.fullmatch(x) for x in v))


def _check_event(e):
    """單筆事件的欄位驗證；回錯誤訊息 list。"""
    if not isinstance(e, dict):
        return ["事件須為 JSON object（一行一事件）"]
    errs = []
    etype = e.get("type")
    schema = EVENT_SCHEMAS.get(etype)
    if schema is None:
        return [f"未知 type「{etype}」（合法：{'/'.join(EVENT_SCHEMAS)}）"]
    for k in schema["required"]:
        if k not in e:
            errs.append(f"缺必填欄位「{k}」")
    allowed = set(schema["required"]) | set(schema["optional"])
    for k in e:
        if k not in allowed:
            errs.append(f"未知欄位「{k}」")
    if errs:
        return errs
    if not RE_DATE.fullmatch(str(e["date"])):
        errs.append(f"date 格式須為 YYYY-MM-DD：{e['date']!r}")
    if etype == "feature_close":
        if not RE_FEATURE.fullmatch(str(e["feature"])):
            errs.append(f"feature 格式須為 NNN-slug：{e['feature']!r}")
        if not RE_SHA.fullmatch(str(e["merge"])):
            errs.append(f"merge 須為 git SHA：{e['merge']!r}")
        pins = e["pins"]
        if not (isinstance(pins, dict) and set(pins) == {"web", "api"}
                and all(RE_SHA.fullmatch(str(v)) for v in pins.values())):
            errs.append('pins 須為 {"web": SHA, "api": SHA}')
        if not _id_list_ok(e["adrs"], RE_ADR_ID):
            errs.append("adrs 須為 4 位 ADR 編號字串 list（可空）")
        ai = e["arch_impact"]
        if not (ai == "none" or (isinstance(ai, list) and ai
                                 and all(isinstance(x, str) and RE_SECTION.fullmatch(x)
                                         for x in ai))):
            errs.append('arch_impact 須為 ["§N", …] 或 "none"')
        for k in ("backlog_add", "backlog_done"):
            if not _id_list_ok(e[k], RE_BID):
                errs.append(f"{k} 須為 B-NNN 字串 list（可空）")
        if "kind" in e and e["kind"] not in ("vertical", "horizontal"):
            errs.append('kind 須為 "vertical"|"horizontal"')
        if "spec_supersessions" in e:
            ss = e["spec_supersessions"]
            if not (isinstance(ss, list) and all(
                    isinstance(x, dict) and set(x) == {"feature", "item", "note"}
                    for x in ss)):
                errs.append("spec_supersessions 須為 [{feature,item,note},…]")
    elif etype == "review":
        fd = e["findings"]
        if not (isinstance(fd, dict)
                and set(fd) == {"total", "fixed", "to_backlog", "wontfix_adr"}
                and isinstance(fd.get("total"), int) and fd["total"] >= 0
                and isinstance(fd.get("fixed"), int) and fd["fixed"] >= 0
                and _id_list_ok(fd.get("to_backlog"), RE_BID)
                and _id_list_ok(fd.get("wontfix_adr"), RE_ADR_ID)):
            errs.append("findings 須為 {total≥0, fixed≥0, to_backlog[B-NNN…], wontfix_adr[00NN…]}")
        elif fd["fixed"] + len(fd["to_backlog"]) + len(fd["wontfix_adr"]) != fd["total"]:
            errs.append("findings 分流不守恆：fixed＋len(to_backlog)＋len(wontfix_adr) 須＝total")
    elif etype == "misc":
        if "backlog_done" in e and not _id_list_ok(e["backlog_done"], RE_BID):
            errs.append("backlog_done 須為 B-NNN 字串 list（可空）")
    return errs


def _jsonl_lines(text):
    """jsonl 行界只認 \\n（splitlines 會在 U+2028 等處誤切合法 JSON 字串）。"""
    lines = (text or "").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [l.rstrip("\r") for l in lines]


def lint_events(text):
    """L3：ops/events.jsonl 逐行 JSON Schema 驗證。回 findings list。"""
    out = []
    for n, line in enumerate(_jsonl_lines(text), start=1):
        where = f"{EVENTS}:行 {n}"
        if not line.strip():
            out.append(finding(ERROR, "L3", where, "不得有空行（jsonl 一行一事件）"))
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError as ex:
            out.append(finding(ERROR, "L3", where, f"非合法 JSON：{ex.msg}"))
            continue
        for msg in _check_event(e):
            out.append(finding(ERROR, "L3", where, msg))
    return out


# L7 預算表：rel path → (行數上限, token 上限)；None＝不設
BUDGETS = {
    "README.md": (150, None),
    "CLAUDE.md": (250, None),
    "docs/ops/NOTES.md": (40, None),
    "docs/ops/BACKLOG.md": (200, None),
    "docs/generated/STATE.md": (None, 4000),
    "docs/arc42/ARCHITECTURE.md": (700, 25000),
}
LESSONS_TOKEN_LIMIT = 25000
LESSONS_TOKEN_WARN = 22500
BACKLOG_VOL_LINE_LIMIT = 200
# 活書單節配額（行數、超出＝警告）
SECTION_QUOTAS = {1: 40, 2: 30, 3: 50, 4: 40, 5: 90, 6: 120,
                  7: 60, 8: 90, 9: 5, 10: 40, 11: 3, 12: 30}
RE_BOOK_SECTION = re.compile(r"^## §(\d{1,2})\b")


def _read(root, rel):
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8-sig") as fh:  # -sig：吞 BOM（Windows 編輯器常見）
        return fh.read()


def _line_count(text):
    return len(text.splitlines())


def lint_budgets(root):
    """L7：檔案預算（行數／token）＋活書單節配額。回 findings list。"""
    out = []
    for rel, (max_lines, max_tokens) in BUDGETS.items():
        text = _read(root, rel)
        if text is None:
            continue
        if max_lines is not None and _line_count(text) > max_lines:
            out.append(finding(ERROR, "L7", rel,
                               f"行數 {_line_count(text)} 超出預算 {max_lines}"))
        if max_tokens is not None and token_count(text) > max_tokens:
            out.append(finding(ERROR, "L7", rel,
                               f"約 {token_count(text)} tokens 超出預算 {max_tokens}"))
    # LESSONS 全卷（LESSONS.md＋LESSONS-*.md）各卷 token 限額；BACKLOG 卷（BACKLOG-*.md）
    # 各卷行數限額（同主檔 200）——皆走 glob、新卷免登記 BUDGETS 即被涵蓋
    ops_dir = os.path.join(root, "docs/ops")
    if os.path.isdir(ops_dir):
        for name in sorted(os.listdir(ops_dir)):
            rel = f"docs/ops/{name}"
            if name == "LESSONS.md" or (name.startswith("LESSONS-") and name.endswith(".md")):
                toks = token_count(_read(root, rel))
                if toks > LESSONS_TOKEN_LIMIT:
                    out.append(finding(ERROR, "L7", rel,
                                       f"約 {toks} tokens 超出單卷上限 {LESSONS_TOKEN_LIMIT}——請分卷（詳活書文件規則）"))
                elif toks > LESSONS_TOKEN_WARN:
                    out.append(finding(WARN, "L7", rel,
                                       f"約 {toks} tokens 逼近單卷上限 {LESSONS_TOKEN_LIMIT}，宜準備分卷"))
            elif name.startswith("BACKLOG-") and name.endswith(".md"):
                lines = _line_count(_read(root, rel) or "")
                if lines > BACKLOG_VOL_LINE_LIMIT:
                    out.append(finding(ERROR, "L7", rel,
                                       f"行數 {lines} 超出單卷預算 {BACKLOG_VOL_LINE_LIMIT}"))
    # 活書單節配額（警告級）
    book = _read(root, BOOK)
    if book is not None:
        for sec, count in book_section_lines(book).items():
            quota = SECTION_QUOTAS.get(sec)
            if quota is not None and count > quota:
                out.append(finding(WARN, "L7", BOOK,
                                   f"§{sec} 共 {count} 行超出單節配額 {quota}"))
    return out


# ---------------------------------------------------------------------------
# L8 ADR／L9 ID／L10 時態／L11 詞典
# ---------------------------------------------------------------------------


RE_ADR_FILENAME = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9-]*\.md$")
ADR_STATUSES = ("draft", "accepted", "superseded", "rejected")
ADR_REQUIRED = ("id", "title", "date", "status")
# accepted 後仍可動的 front-matter 欄：superseded_by（工具回填）；status 僅可轉 superseded
ADR_MUTABLE_AFTER_ACCEPT = ("superseded_by",)


def _adr_list(meta, key):
    v = meta.get(key, [])
    return v if isinstance(v, list) else None


def _valid_adr_id(v):
    return isinstance(v, str) and bool(RE_ADR_ID.fullmatch(v))


def lint_adrs(adrs, head_adrs, amend=False):
    """L8：ADR front-matter schema＋accepted 不可變＋supersedes 對稱＋禁刪除。

    adrs / head_adrs：{filename: 檔案全文}（head_adrs＝git HEAD 版；無 HEAD 版＝空 dict）。
    amend=True（env DOCS_SYNC_ADR_AMEND=1）＝豁免 accepted body 不可變（typo 級修正）。
    """
    out = []
    for fn in head_adrs:
        if fn not in adrs:
            out.append(finding(ERROR, "L8", f"{ADR_DIR}/{fn}",
                               "ADR 禁刪除（編號永不重用；翻案＝新檔 supersedes）"))
    metas = {}
    for fn, text in sorted(adrs.items()):
        where = f"{ADR_DIR}/{fn}"
        meta, body = parse_front_matter(text)
        metas[fn] = (meta, body)
        m = RE_ADR_FILENAME.fullmatch(fn)
        if not m:
            out.append(finding(ERROR, "L8", where, "檔名須為 NNNN-<slug>.md"))
        for k in ADR_REQUIRED:
            if k not in meta:
                out.append(finding(ERROR, "L8", where, f"front-matter 缺必填欄「{k}」"))
        status = meta.get("status")
        if status is not None and status not in ADR_STATUSES:
            out.append(finding(ERROR, "L8", where,
                               f"status 須為 {'|'.join(ADR_STATUSES)}：{status!r}"))
        if "id" in meta and not _valid_adr_id(meta["id"]):
            out.append(finding(ERROR, "L8", where, f"id 須為 4 位數字字串：{meta['id']!r}"))
        if m and _valid_adr_id(meta.get("id")) and meta["id"] != m.group(1):
            out.append(finding(ERROR, "L8", where,
                               f"id「{meta['id']}」與檔名編號「{m.group(1)}」不一致（編號＝檔名）"))
        if "date" in meta and not RE_DATE.fullmatch(str(meta["date"])):
            out.append(finding(ERROR, "L8", where, f"date 格式須為 YYYY-MM-DD：{meta['date']!r}"))
        for k in ("supersedes", "superseded_by"):
            v = _adr_list(meta, k)
            if v is None or not all(RE_ADR_ID.fullmatch(str(x)) for x in v):
                out.append(finding(ERROR, "L8", where, f"{k} 須為 4 位 ADR 編號 list"))
        if "feature" in meta and not isinstance(meta.get("feature"), str):
            out.append(finding(ERROR, "L8", where, "feature 須為字串"))
        if "provenance" in meta and not isinstance(meta.get("provenance"), str):
            out.append(finding(ERROR, "L8", where, "provenance 須為字串"))
        if "tags" in meta and not isinstance(meta.get("tags"), list):
            out.append(finding(ERROR, "L8", where, "tags 須為 list"))
    # 撞號偵測（同號不同 slug 的 merge 不會產生 git 衝突、必須 lint 抓）
    seen_ids = {}
    for fn, (meta, _) in sorted(metas.items()):
        i = meta.get("id")
        if _valid_adr_id(i):
            if i in seen_ids:
                out.append(finding(ERROR, "L8", f"{ADR_DIR}/{fn}",
                                   f"id「{i}」與 {seen_ids[i]} 重複配號（編號永不重用）"))
            else:
                seen_ids[i] = fn
    by_id = {meta["id"]: (fn, meta) for fn, (meta, _) in metas.items()
             if _valid_adr_id(meta.get("id"))}
    for fn, (meta, _) in sorted(metas.items()):
        where = f"{ADR_DIR}/{fn}"
        my_id = meta.get("id")
        for x in (_adr_list(meta, "supersedes") or []):
            x = str(x)
            if x not in by_id:
                out.append(finding(ERROR, "L8", where, f"supersedes 指向不存在的 ADR「{x}」"))
                continue
            _, tmeta = by_id[x]
            if my_id and my_id not in (_adr_list(tmeta, "superseded_by") or []):
                out.append(finding(ERROR, "L8", where,
                                   f"supersedes 對稱缺口：ADR {x} 的 superseded_by 未回填"
                                   f"「{my_id}」（跑 tools/docs-sync.py generate 回填）"))
            if tmeta.get("status") != "superseded":
                out.append(finding(ERROR, "L8", where,
                                   f"被翻案的 ADR {x} status 須為 superseded"))
        for x in (_adr_list(meta, "superseded_by") or []):
            x = str(x)
            if x not in by_id:
                out.append(finding(ERROR, "L8", where, f"superseded_by 指向不存在的 ADR「{x}」"))
            elif my_id and my_id not in (_adr_list(by_id[x][1], "supersedes") or []):
                out.append(finding(ERROR, "L8", where,
                                   f"superseded_by 對稱缺口：ADR {x} 未宣告 supersedes「{my_id}」"))
    for fn, head_text in sorted(head_adrs.items()):
        if fn not in adrs:
            continue
        hmeta, hbody = parse_front_matter(head_text)
        if hmeta.get("status") != "accepted":
            continue
        where = f"{ADR_DIR}/{fn}"
        cmeta, cbody = metas[fn]
        if cbody != hbody and not amend:  # amend 僅豁免 body 的 typo 級修正
            out.append(finding(ERROR, "L8", where,
                               "accepted 後 body 不可變（typo 級修正：commit message 帶"
                               " [adr-amend] 並設 DOCS_SYNC_ADR_AMEND=1）"))
        for k in sorted(set(hmeta) | set(cmeta)):
            if k in ADR_MUTABLE_AFTER_ACCEPT:
                continue
            if k == "status":
                if cmeta.get(k) not in ("accepted", "superseded"):
                    out.append(finding(ERROR, "L8", where,
                                       "accepted 的 status 僅可轉 superseded"))
                continue
            if hmeta.get(k) != cmeta.get(k):
                out.append(finding(ERROR, "L8", where,
                                   f"accepted 後 front-matter 欄「{k}」不可變"))
    return out


RE_NEXT_ID = re.compile(r"<!--\s*next:\s*([BL])-(\d+)\s*-->")
RE_ENTRY = {
    "B": re.compile(r"^- B-(\d+)｜", re.M),
    "L": re.compile(r"^- (?:\*\*)?L-(\d+)(?:\*\*)?｜", re.M),
}
# 反回收豁免視野（L9 head_ids 專用）：不錨行首的寬鬆子串形——｜為欄位分隔、散文引用不帶，
# 故「字串曾在 HEAD 出現」即非回收；格式事故（行黏連/縮排）修復不誤判，真回收（號碼已刪列
# ＝字串已消失）照抓。staged 側計數/撞號仍用嚴格 RE_ENTRY。user 拍板調規 2026-07-19（B-106）。
RE_ENTRY_ANYPOS = {
    "B": re.compile(r"B-(\d+)｜"),
    "L": re.compile(r"L-(\d+)(?:\*\*)?｜"),
}


def _parse_next(kind, text):
    m = RE_NEXT_ID.search(text or "")
    return int(m.group(2)) if m and m.group(1) == kind else None


def lint_ids(kind, texts, head_texts):
    """L9：B-NNN／L-NNN 依檔頭 next-id 驗唯一、單調、不回收。

    kind："B" 或 "L"；texts／head_texts＝[主檔文, 其餘卷文…]（主檔在首、含 next-id 檔頭）。
    head_texts 各元素可為 None（HEAD 無此檔）。
    """
    out = []
    label = {"B": BACKLOG, "L": "docs/ops/LESSONS.md"}[kind]
    cur_next = _parse_next(kind, texts[0])
    if cur_next is None:
        out.append(finding(ERROR, "L9", label, "缺 next-id 檔頭（<!-- next: %s-NNN -->）" % kind))
    ids, seen = [], set()
    for text in texts:
        for m in RE_ENTRY[kind].finditer(text or ""):
            n = int(m.group(1))
            if n in seen:
                out.append(finding(ERROR, "L9", label, f"{kind}-{n:03d} 重複配號"))
            seen.add(n)
            ids.append(n)
    if cur_next is not None:
        for n in ids:
            if n >= cur_next:
                out.append(finding(ERROR, "L9", label,
                                   f"{kind}-{n:03d} ≥ next-id {cur_next}（配號＝取 next 後 bump）"))
    head_next = _parse_next(kind, head_texts[0]) if head_texts else None
    if head_next is not None:
        if cur_next is not None and cur_next < head_next:
            out.append(finding(ERROR, "L9", label,
                               f"next-id 須單調遞增（HEAD {head_next} → 現 {cur_next}）"))
        head_ids = set()
        for text in head_texts:
            head_ids.update(int(m.group(1)) for m in RE_ENTRY_ANYPOS[kind].finditer(text or ""))
        for n in sorted(set(ids) - head_ids):
            if n < head_next:
                out.append(finding(ERROR, "L9", label,
                                   f"{kind}-{n:03d} 為舊號回收（新號必 ≥ HEAD next-id {head_next}；號碼永不回收）"))
    return out


TENSE_WORDS = {
    "待決": "ops/BACKLOG（待辦）或 ADR draft（未決案）",
    "TBD": "ops/BACKLOG",
    "⏳": "ops/BACKLOG",
    "已完成": "git 史＋ops/events.jsonl（過去式不入書）",
    "下一步": "ops/NOTES（未來式不入書）",
}


def lint_tense(book_text):
    """L10：活書時態禁詞（待決/TBD/⏳/已完成/下一步），附去處提示。"""
    out = []
    for n, line in enumerate(book_text.splitlines(), start=1):
        for word, dest in TENSE_WORDS.items():
            if word in line:
                out.append(finding(ERROR, "L10", f"{BOOK}:行 {n}",
                                   f"活書時態禁詞「{word}」；去處：{dest}"))
    return out


DICT_PATTERNS = (
    (re.compile(r"⚠️[a-z]+"), "rev3 決策碼走私", "內容過境、編號不過境——改寫為自解釋描述"),
    (re.compile(r"待決[①②③④⑤⑥⑦⑧⑨⑩]"), "rev3 待決碼走私", "內容過境、編號不過境——改寫為自解釋描述"),
    (re.compile(r"\bF-\d+\b"), "rev3 流水碼走私", "內容過境、編號不過境——改寫為自解釋描述"),
    (re.compile(r"(?i)\bport\s*[:=]?\s*\d{2,5}\b"), "port 實值",
     "快變字面值不入活文件→ docs/generated/reference/ports.md"),
    (re.compile(r"(?<![0-9a-fA-F])123456(?![0-9a-fA-F])"), "seed 密碼實值",
     "快變字面值不入活文件→ docs/generated/reference/accounts.md"),
    (re.compile(r"(?i)(?:routes?|路由|端點|endpoints?)\D{0,8}?\d+"
                r"|\d+\s*(?:條|個|支)?\s*(?:routes?|路由|端點|endpoints?)"), "route 計數實值",
     "快變字面值不入活文件→ docs/generated/reference/routes.md"),
)


def lint_dictionary(texts):
    """L11：禁入詞典（警告級）。texts＝{rel: 全文}，掃活書＋CLAUDE.md。

    「｜出處：」起始的行（rev3 史料標註）整行豁免——僅行首、行中不豁免。
    """
    out = []
    for rel, text in sorted(texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            if line.lstrip().startswith("｜出處："):
                continue
            for pat, label, hint in DICT_PATTERNS:
                for m in pat.finditer(line):
                    out.append(finding(WARN, "L11", f"{rel}:行 {n}",
                                       f"禁入詞典命中「{m.group(0)}」（{label}）；{hint}"))
    return out


# ---------------------------------------------------------------------------
# L12~L15 引用健康
# ---------------------------------------------------------------------------


RE_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
RE_LINE_REF = re.compile(r"\S+\.md:\d+")
# BACKLOG 全系（含 BACKLOG-*.md 卷）皆揮發故一律禁錨；LESSONS 系 append-only、錨穩定故不禁
RE_VOLATILE_ANCHOR = re.compile(r"(?:BACKLOG(?:-[A-Za-z0-9-]+)?|NOTES|STATE)\.md#\S+")
RE_MEMORY_PATH = re.compile(r"(?:~|/home/[^/\s]+)/\.claude/[^\s)]*")


def _iter_links(md_texts):
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_MD_LINK.finditer(line):
                yield rel, n, m.group(1)


def lint_links(md_texts, existing_paths):
    """L12：md 內部連結（相對路徑）必須指向存在檔案。

    md_texts＝{rel: 全文}；existing_paths＝repo 現存（git 追蹤）路徑 set。
    http(s)/mailto/純錨點連結不驗。
    """
    out = []
    for rel, n, target in _iter_links(md_texts):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#", 1)[0]
        resolved = os.path.normpath(os.path.join(os.path.dirname(rel), path)).replace(os.sep, "/")
        if resolved not in existing_paths:
            out.append(finding(ERROR, "L12", f"{rel}:行 {n}",
                               f"連結指向不存在檔案「{target}」（解析為 {resolved}）"))
    return out


def lint_line_refs(md_texts):
    """L13：禁行號引用（xxx.md:123 型）——行號揮發、引用必 rot。"""
    out = []
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_LINE_REF.finditer(line):
                out.append(finding(ERROR, "L13", f"{rel}:行 {n}",
                                   f"禁行號引用「{m.group(0)}」；改用穩定語意錨（節號／檔名／描述名）"))
    return out


def lint_volatile_deep_links(md_texts):
    """L14：禁 deep-link 揮發區內部錨（BACKLOG/NOTES/STATE 只可整檔引用）。"""
    out = []
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_VOLATILE_ANCHOR.finditer(line):
                out.append(finding(ERROR, "L14", f"{rel}:行 {n}",
                                   f"揮發區禁 deep-link「{m.group(0)}」；只可整檔引用"))
    return out


def lint_memory_refs(md_texts):
    """L15：repo 文件禁引 per-machine memory 實路徑（~/.claude/**）。

    帶 rev3: 前綴的純文字史料標註（如 rev3:memory/…）非實路徑、天然不命中。
    """
    out = []
    for rel, text in sorted(md_texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            for m in RE_MEMORY_PATH.finditer(line):
                out.append(finding(ERROR, "L15", f"{rel}:行 {n}",
                                   f"禁引 per-machine 路徑「{m.group(0)}」；先提取進 repo 文件再引用"))
    return out


# ---------------------------------------------------------------------------
# L16 憑證內容掃描（contracts G1／data-model §1§2；ADR 0077）
# ---------------------------------------------------------------------------

# 窄集合高確信樣式：刻意**不含**泛熵值與 password= 類（誤報成本高於殘餘風險——漏報面有意識
# 接受）。擴充或豁免一律動本常數＋立 ADR；無 inline 豁免 marker（防偽）。
CRED_PATTERNS = (
    ("pem-private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY( BLOCK)?-----")),
    ("aws-akia", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,255}\b")),
)
CRED_WHITELIST = ()            # 豁免白名單（現空集；擴充須同時立 ADR——ADR 0077 豁免路徑）
CRED_SUBMODULES = ("base-web", "rust-api")
CRED_BINARY_PROBE = 8192       # 前 8KB 含 NUL byte 即判二進位（近似 git 的偵測、憑證必為文字）


def scan_cred_text(text):
    """全文過樣式集；回 [(label, 行號)]（同 label 只回首命中，訊息不爆量）。"""
    hits = []
    for label, pat in CRED_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append((label, text.count("\n", 0, m.start()) + 1))
    return hits


def _cred_samples():
    """self-test 紅綠樣本。

    ★執行期字串串接構造：本檔屬 tracked，落任何完整命中字面即被外層全量掃自命中自紅。
    """
    red = [
        ("pem-private-key", "-----BEGIN " + "RSA PRIVATE" + " KEY" + "-----"),
        ("aws-akia", "AKIA" + "0123456789ABCDEF"),
        ("github-token", "gh" + "p_" + "s3lfT3st" * 4 + "Samp"),
        ("github-pat", "github" + "_pat_" + "s3lfT3stSampl3Str1ng0k"),
    ]
    green = ["普通說明文字、無憑證內容。", "-----BEGIN CERTIFICATE-----",
             "AKIA" + "TOOSHORT", "gh" + "p_" + "short"]
    return red, green


def cred_self_test():
    """防恆綠：每次 lint 連帶驗紅樣本必紅、綠樣本必綠；失效即 ERROR（contracts G1）。"""
    out = []
    red, green = _cred_samples()
    for label, sample in red:
        if label not in [l for l, _ in scan_cred_text(sample)]:
            out.append(finding(ERROR, "L16", "tools/docs-sync.py",
                               f"憑證掃描 self-test 失效：紅樣本 {label} 未被攔下"
                               "——條款已恆綠，修復 CRED_PATTERNS 後重跑"))
    for sample in green:
        hit = scan_cred_text(sample)
        if hit:
            out.append(finding(ERROR, "L16", "tools/docs-sync.py",
                               f"憑證掃描 self-test 失效：綠樣本誤報 {hit[0][0]}"
                               "——樣式集過寬，收窄後重跑"))
    return out


def cred_diff_hits(diff_text):
    """unified diff（-U0）新增行過樣式集；回 [(檔路徑, label)]。

    ★以 hunk 狀態機判檔頭、不以前綴猜測：-U0 的內容行本身帶一個 `+` 前綴，故檔案內任何
    以「兩個加號加空白」起首的行，在 diff 裡就長成三個加號加空白——單看前綴會把它當檔頭
    整行吞掉（該行漏掃），且把行內容寫進路徑欄（其後真命中被指名到不存在的檔）。狀態機
    界線嚴密：檔頭必在該檔首個 `@@` 之前、內容行必在 `@@` 之後。
    """
    out, path, in_hunk = [], "?", False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            path, in_hunk = "?", False
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk and line.startswith("+++ "):
            raw = line[4:].strip()
            path = raw[2:] if raw.startswith(("a/", "b/")) else raw
            continue
        if not line.startswith("+"):
            continue
        for label, _n in scan_cred_text(line[1:]):
            if (path, label) not in out:
                out.append((path, label))
    return out


# ---------------------------------------------------------------------------
# generate／check／errata
# ---------------------------------------------------------------------------

GEN_HEADER = "<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->"
REFERENCE_TABLES = ("routes", "ports", "schema", "accounts", "screens")
# stub 轉真的表：STATE 對賬行改列真來源描述（其餘表維持 gen_reference_stub）
REFERENCE_LIVE = {
    "routes": "真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）",
    "ports": "真表（來源＝compose 三檔的 ports: 段、由 generate 重算）",
    "schema": "真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、"
              "由 generate 重算；快照由 refresh 自實庫撈）",
    "accounts": "真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；"
                "快照由 refresh 自實庫撈）",
    "screens": "真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、"
               "由 generate 重算；全巢狀 route flatten）",
}
# ports 對照表來源（base 層設計鐵律禁 host ports、映射只住 dev/example）
COMPOSE_FILES = ("docker-compose.yml", "docker-compose.dev.yml", "docker-compose.example.yml")
# backend 拒因字典鏈（B-007／FR-014）常數——生成器本體見下方「backend 拒因字典鏈」節
MSG_DICT_LOCALES = (("zh-TW", "base-web/src/locales/langs/zh-tw.ts"),
                    ("en-US", "base-web/src/locales/langs/en-us.ts"))
MSG_DICT_MD = f"{GENERATED_DIR}/reference/backend-msg-dict.md"
MSG_DICT_PANEL = "deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json"
MSG_DICT_HINT = ("機器生成：tools/docs-sync.py generate（來源＝base-web locale backend.* 兩語）"
                 "——嚴禁手改；差異由 pre-commit check 攔下")


DEFAULT_BRANCH = "rev4-admin-root"


def _md_cell(v):
    s = str(v) if v not in (None, "", []) else "—"
    return s.replace("|", "\\|")


def _event_row(e):
    t = e.get("type", "?")
    target = {"feature_close": e.get("feature"), "review": e.get("scope")}.get(t)
    merge = e.get("merge") if t == "feature_close" else None
    adrs = "、".join(e.get("adrs", [])) if t == "feature_close" else None
    ai = e.get("arch_impact") if t == "feature_close" else None
    arch = "、".join(ai) if isinstance(ai, list) else ai
    return (f"| {_md_cell(e.get('date'))} | {_md_cell(t)} | {_md_cell(target)} "
            f"| {_md_cell(e.get('summary') or e.get('report'))} | {_md_cell(merge)} "
            f"| {_md_cell(adrs)} | {_md_cell(arch)} |")


MILESTONE_TABLE_HEAD = ("| date | type | 標的 | summary | merge | adrs | arch |\n"
                        "|---|---|---|---|---|---|---|")


def gen_milestones(events):
    """MILESTONES ← 全 events 表格化、按年分卷。回 {rel: content}。

    date 畸形的事件（generate 走寬鬆解析、不等 L3）一律留在主卷，
    不得以字串序劫走 max(year) 的主卷位置。
    """
    by_year, stray = {}, []
    for e in events:
        d = str(e.get("date", ""))
        if RE_DATE.fullmatch(d):
            by_year.setdefault(d[:4], []).append(e)
        else:
            stray.append(e)
    if not by_year and not stray:
        return {f"{GENERATED_DIR}/MILESTONES.md":
                f"{GEN_HEADER}\n# MILESTONES — 全事件表\n\n（尚無事件）\n"}
    cur = max(by_year) if by_year else "？"
    by_year.setdefault(cur, []).extend(stray)
    out = {}
    for year, evs in by_year.items():
        rel = (f"{GENERATED_DIR}/MILESTONES.md" if year == cur
               else f"{GENERATED_DIR}/MILESTONES-{year}.md")
        rows = "\n".join(_event_row(e) for e in evs)
        out[rel] = (f"{GEN_HEADER}\n# MILESTONES — 全事件表（{year}）\n\n"
                    f"{MILESTONE_TABLE_HEAD}\n{rows}\n")
    return out


def gen_decisions_index(metas):
    """DECISIONS-INDEX ← ADR front-matter 掃描。metas＝[{…}]（依 id 排序輸出）。"""
    head = f"{GEN_HEADER}\n# DECISIONS-INDEX — ADR 索引\n\n"
    if not metas:
        return head + "（尚無 ADR）\n"
    rows = []
    for m in sorted(metas, key=lambda m: str(m.get("id", ""))):
        rows.append(
            f"| {_md_cell(m.get('id'))} | {_md_cell(m.get('status'))} "
            f"| {_md_cell(m.get('date'))} | {_md_cell(m.get('title'))} "
            f"| {_md_cell(m.get('feature'))} "
            f"| {_md_cell('、'.join(m.get('supersedes', []) or []))} "
            f"| {_md_cell('、'.join(m.get('superseded_by', []) or []))} |")
    return (head + "| id | status | date | title | feature | supersedes | superseded_by |\n"
            "|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")


def _fmt_pin(sha):
    return sha[:7] if sha else "未建置"


def gen_state(ctx):
    """STATE ← events 尾 3 筆＋pins＋constitution 版本＋統計＋對賬結果。"""
    events = ctx.get("events", [])
    adr_metas = ctx.get("adr_metas", [])
    status_count = {}
    for m in adr_metas:
        status_count[m.get("status", "?")] = status_count.get(m.get("status", "?"), 0) + 1
    adr_stat = ("、".join(f"{k} {v}" for k, v in sorted(status_count.items()))
                if status_count else "0")
    type_count = {}
    for e in events:
        type_count[e.get("type", "?")] = type_count.get(e.get("type", "?"), 0) + 1
    ev_stat = ("、".join(f"{k} {v}" for k, v in sorted(type_count.items()))
               if type_count else "0")
    tail = list(reversed(events[-3:]))
    if tail:
        tail_lines = "\n".join(
            f"- {e.get('date')}｜{e.get('type')}｜"
            + (f"{e.get('feature')}｜" if e.get("feature") else "")
            + str(e.get("summary") or e.get("scope") or "")
            for e in tail)
    else:
        tail_lines = "（尚無事件）"
    bn = ctx.get("backlog_next")
    ln = ctx.get("lessons_next")
    ref_lines = "\n".join(
        f"- reference/{name}：" + REFERENCE_LIVE.get(
            name, "stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）")
        for name in REFERENCE_TABLES)
    return f"""{GEN_HEADER}
# STATE — 現況機器帳

## git
- default branch：{DEFAULT_BRANCH}
- pins：base-web={_fmt_pin(ctx.get('pins', {}).get('web'))}｜rust-api={_fmt_pin(ctx.get('pins', {}).get('api'))}

## constitution
- 版本：{ctx.get('constitution_version') or '未鑄'}

## 帳面統計
- ADR：{len(adr_metas)}（{adr_stat}）
- BACKLOG 待辦：{ctx.get('backlog_count', 0)}（next：{f'B-{bn:03d}' if bn else '？'}）｜滯後：{ctx.get('backlog_deferred_count', 0)}
- LESSONS：{ctx.get('lessons_count', 0)} 筆（next：{f'L-{ln:03d}' if ln else '？'}）
- events：{len(events)} 筆（{ev_stat}）

## 最近事件（尾 3 筆、新在前）
{tail_lines}

## reference 對賬
{ref_lines}
"""


def _set_fm_field(text, key, value_line):
    """就地改寫 front-matter 單欄（存在則替換、不存在則插在關閉 --- 前）。"""
    lines = text.splitlines(keepends=True)
    close = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close = i
            break
    if close is None:
        return text
    for i in range(1, close):
        if lines[i].split(":", 1)[0].strip() == key:
            lines[i] = value_line + "\n"
            return "".join(lines)
    lines.insert(close, value_line + "\n")
    return "".join(lines)


def backfill_supersessions(adrs):
    """supersedes 對稱回填：A supersedes X ⇒ X.superseded_by ∋ A.id 且 X.status=superseded。

    adrs＝{filename: 全文}；回 {filename: 新全文}（僅含需要改的檔）。
    """
    metas = {fn: parse_front_matter(text)[0] for fn, text in adrs.items()}
    by_id = {m["id"]: fn for fn, m in metas.items() if _valid_adr_id(m.get("id"))}
    changed = {}
    for fn, m in sorted(metas.items()):
        if not _valid_adr_id(m.get("id")):
            continue  # 缺 id／畸形 id 由 L8 報，此處不崩
        for x in (_adr_list(m, "supersedes") or []):
            tfn = by_id.get(str(x))
            if tfn is None:
                continue  # dangling → L8 擋，不在此處理
            cur_text = changed.get(tfn, adrs[tfn])
            tmeta = parse_front_matter(cur_text)[0]
            sb = list(_adr_list(tmeta, "superseded_by") or [])
            new_text = cur_text
            if m["id"] not in sb:
                sb.append(m["id"])
                new_text = _set_fm_field(new_text, "superseded_by",
                                         f"superseded_by: [{', '.join(sorted(sb))}]")
            if tmeta.get("status") != "superseded":
                new_text = _set_fm_field(new_text, "status", "status: superseded")
            if new_text != adrs[tfn]:
                changed[tfn] = new_text
    return changed


def errata_scan(texts, keyword):
    """errata：全 repo 同語意（大小寫不敏感子串）枚舉。回 [(rel, 行號, 行文)]。"""
    kw = keyword.lower()
    hits = []
    for rel, text in sorted(texts.items()):
        for n, line in enumerate((text or "").splitlines(), start=1):
            if kw in line.lower():
                hits.append((rel, n, line))
    return hits


# L2 對賬：轉真表各有真來源——漂移指名來源側（其餘生成檔漂移歸 L1 泛訊息）
L2_SOURCES = {
    f"{GENERATED_DIR}/reference/routes.md":
        "routes 對照表與 router.rs 重算結果不一致——"
        "rust-api/server/src/router.rs ROUTES 改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/ports.md":
        "ports 對照表與 compose 重算結果不一致——compose 三檔"
        " ports: 段改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/schema.md":
        "schema 正典表與快照重算結果不一致——docs/ops/reference-src/schema-snapshot.json"
        "（或 archetype-map.json）改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/accounts.md":
        "accounts 正典表與快照重算結果不一致——docs/ops/reference-src/"
        "accounts-snapshot.json 改動後未跑 tools/docs-sync.py generate",
    f"{GENERATED_DIR}/reference/screens.md":
        "screens 正典表與 routes.ts 重算結果不一致——"
        "base-web/src/router/elegant/routes.ts 的 generatedRoutes 改動後未跑 tools/docs-sync.py generate",
    MSG_DICT_MD:
        "backend 拒因字典與 locale 重算結果不一致——base-web/src/locales/langs/"
        "{zh-tw,en-us}.ts 的 backend.* 改動後未跑 tools/docs-sync.py generate",
    MSG_DICT_PANEL:
        "字典面板 json 與 locale 重算結果不一致——deploy 側生成物嚴禁手改；"
        "locale 改動後跑 tools/docs-sync.py generate（FR-014 守門）",
}


def check_generated(root, computed):
    """check：computed（{rel: content}）與磁碟現況 diff。回 findings。"""
    out = []
    gen_root = os.path.join(root, GENERATED_DIR)
    on_disk = set()
    for dirpath, _, names in os.walk(gen_root):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            on_disk.add(rel)
    # deploy 側字典面板＝生成物治外飛地（僅此一檔納管；同目錄手寫面板不受掃描）
    if os.path.exists(os.path.join(root, MSG_DICT_PANEL)):
        on_disk.add(MSG_DICT_PANEL)
    for rel in sorted(set(computed) | on_disk):
        if rel not in computed:
            out.append(finding(ERROR, "L1", rel, "多出的檔案（generated/ 嚴禁手加；請移除）"))
        elif rel not in on_disk:
            out.append(finding(ERROR, "L1", rel, "缺生成檔（跑 tools/docs-sync.py generate）"))
        elif _read(root, rel) != computed[rel]:
            if rel in L2_SOURCES:
                out.append(finding(ERROR, "L2", rel, L2_SOURCES[rel]))
            else:
                out.append(finding(ERROR, "L1", rel,
                                   "與重算結果不一致（忘跑 generate 或手改；跑 tools/docs-sync.py generate）"))
    return out


# ---------------------------------------------------------------------------
# git 介接與 IO 組裝（薄層；核心邏輯皆為上方可測純函式）
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 史料豁免：內容類 lint（L11~L15）不掃 one-shot 史料（其內文含示例 pattern、必自撞）
HISTORICAL_EXEMPT = ("docs/brainstorms/",)


def _is_exempt(rel):
    return any(rel == p or rel.startswith(p) for p in HISTORICAL_EXEMPT)


def git_out(args, cwd):
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=cwd,
                           capture_output=True, encoding="utf-8", errors="replace")
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def git_available(root):
    """守門工具的 fail-closed 前提：git 本體與 repo 必須可用。"""
    return git_out(["rev-parse", "--git-dir"], root) is not None


def head_file(rel, root):
    return git_out(["show", f"HEAD:{rel}"], root)


def index_pins(root):
    out = git_out(["ls-files", "-s", "--", "base-web", "rust-api"], root) or ""
    pins = {"web": None, "api": None}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "160000":
            pins[{"base-web": "web", "rust-api": "api"}.get(parts[3], "")] = parts[1]
    pins.pop("", None)
    return {"web": pins.get("web"), "api": pins.get("api")}


def tracked_files(root):
    return [l for l in (git_out(["ls-files"], root) or "").splitlines() if l]


def unstaged_generated(root):
    """生成物的 working tree 與 index 落差（跑了 generate 忘了 git add）。"""
    out = git_out(["diff", "--name-only", "--", GENERATED_DIR, MSG_DICT_PANEL], root)
    return [l for l in (out or "").splitlines() if l]


def constitution_version(root):
    text = _read(root, ".specify/memory/constitution.md")
    if text is None:
        return None
    m = re.search(r"\*\*Version\*\*[:\s]*v?(\d+\.\d+\.\d+)", text)
    return m.group(1) if m else None


def load_adrs(root):
    d = os.path.join(root, ADR_DIR)
    if not os.path.isdir(d):
        return {}
    return {n: _read(root, f"{ADR_DIR}/{n}")
            for n in sorted(os.listdir(d)) if n.endswith(".md")}


def load_head_adrs(root):
    """HEAD 版 ADR 全載——單支 cat-file --batch（ADR 數量只增不減、逐檔 git show 會吃穿秒級預算）。"""
    out = git_out(["ls-tree", "HEAD", f"{ADR_DIR}/"], root) or ""
    entries = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        meta_part, path = line.split("\t", 1)
        parts = meta_part.split()
        if len(parts) == 3 and parts[1] == "blob" and path.endswith(".md"):
            entries.append((parts[2], os.path.basename(path)))
    if not entries:
        return {}
    try:
        r = subprocess.run(["git", "cat-file", "--batch"], cwd=root,
                           input="\n".join(oid for oid, _ in entries).encode(),
                           capture_output=True)
    except OSError:
        return {}
    if r.returncode != 0:
        return {}
    head, buf, pos = {}, r.stdout, 0
    for _, name in entries:
        nl = buf.index(b"\n", pos)
        hdr = buf[pos:nl].decode("utf-8", errors="replace").split()
        if len(hdr) != 3 or hdr[1] != "blob":
            pos = nl + 1
            continue
        size = int(hdr[2])
        head[name] = buf[nl + 1: nl + 1 + size].decode("utf-8", errors="replace")
        pos = nl + 1 + size + 1
    return head


def _volume_paths(root, main_rel, prefix):
    """主檔＋docs/ops 下同前綴分卷（sorted）；主檔恆在 index 0。"""
    ops = os.path.join(root, "docs/ops")
    vols = (sorted(n for n in os.listdir(ops)
                   if n.startswith(prefix) and n.endswith(".md"))
            if os.path.isdir(ops) else [])
    return [main_rel] + [f"docs/ops/{v}" for v in vols]


def lessons_paths(root):
    return _volume_paths(root, "docs/ops/LESSONS.md", "LESSONS-")


def backlog_paths(root):
    """BACKLOG 全卷：主檔＋滯後卷（BACKLOG-*.md；滯後≠完成、條目仍屬開放待辦）。
    配號 next-id 只在主檔（texts[0]）；滯後卷收 user 拍板滯後之整行搬移條目。"""
    return _volume_paths(root, BACKLOG, "BACKLOG-")


def gen_reference_stub(name):
    return (f"{GEN_HEADER}\n# reference/{name} — 全量正典表\n\n"
            f"狀態：stub｜來源未就緒——extractor 隨對應子系統首刀落地（見 ops/BACKLOG）。\n")


class ComposePortsError(Exception):
    """compose ports 解析失敗（fail-loud：寧可擋下、不靜默漏列）。"""


# 窄假設唯一合法項形：引號短語法＋127.0.0.1 綁定前綴＋純數字 port（本 repo 實際使用的形；
# 配號紀律歸 ADR 0019）。其他寫法（無引號、0.0.0.0、port 範圍、長語法…）一律 fail-loud。
RE_PORTS_ITEM = re.compile(r'^"(127\.0\.0\.1):(\d{1,5}):(\d{1,5})"$')
RE_COMPOSE_SERVICE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):$")


def parse_compose_ports(text, rel):
    """解析單一 compose 檔的 ports: 段。回 [(service, host_port, container_port, bind_ip)]。

    行級窄假設解析（標準庫、不引 YAML 庫；只支援本 repo 實際使用的形）：
    - 頂層 services:（0 縮排）→ 服務名＝2 縮排 `name:` → ports:＝4 縮排服務直屬鍵
    - 項目＝同縮排或更深縮排的 `- "127.0.0.1:HOST:CONTAINER"`（RE_PORTS_ITEM；不支援行內註解）
    - 任何不認得的 ports 項／ports 鍵位置／services 直屬 2 縮排行 → ComposePortsError 指名檔與行
      ——防未來 compose 改寫法時對照表靜默漏列（fail-loud 逼人同步擴充解析器）
    """
    rows = []
    in_services, service, ports_indent = False, None, None
    for n, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue  # 空行／註解行不終結區塊
        indent = len(raw) - len(raw.lstrip(" "))
        if ports_indent is not None:
            # 項目可與 ports: 鍵同縮排（YAML 合法形）——同縮排非清單行才是區塊結束
            if indent > ports_indent or (indent == ports_indent
                                         and stripped.startswith("- ")):
                if not stripped.startswith("- "):
                    raise ComposePortsError(
                        f"{rel}:行 {n}｜ports 段內不認得的行「{stripped}」（僅支援引號短語法清單項）")
                m = RE_PORTS_ITEM.fullmatch(stripped[2:].strip())
                if not m:
                    raise ComposePortsError(
                        f"{rel}:行 {n}｜不認得的 ports 項「{stripped}」"
                        '（僅支援 - "127.0.0.1:HOST:CONTAINER"；compose 改寫法請同步擴充本解析器）')
                rows.append((service, m.group(2), m.group(3), m.group(1)))
                continue
            ports_indent = None  # 區塊結束、本行落回狀態機
        if indent == 0:
            in_services = (stripped == "services:")
            service = None
            continue
        if stripped.startswith("ports:"):
            if not (in_services and service and indent == 4 and stripped == "ports:"):
                raise ComposePortsError(
                    f"{rel}:行 {n}｜不認得的 ports 鍵寫法/位置「{stripped}」"
                    "（僅支援服務直屬 4 縮排純鍵；compose 改寫法請同步擴充本解析器）")
            ports_indent = indent
            continue
        if in_services and indent == 2:
            m = RE_COMPOSE_SERVICE.fullmatch(stripped)
            if not m:
                raise ComposePortsError(
                    f"{rel}:行 {n}｜services 下不認得的服務行「{stripped}」"
                    "（僅支援裸服務名鍵、不支援行內註解；compose 改寫法請同步擴充本解析器）"
                    "——否則後續 ports 會錯掛到前一個服務")
            service = m.group(1)
    return rows


def compute_ports_rows(root):
    """三檔 compose 全掃。回 [(來源檔, service, host, container, ip)]；來源檔缺＝fail-loud。"""
    rows = []
    for rel in COMPOSE_FILES:
        text = _read(root, rel)
        if text is None:
            raise ComposePortsError(f"{rel}｜compose 來源檔不存在——ports 對照表無法重算")
        rows += [(rel, *r) for r in parse_compose_ports(text, rel)]
    return rows


def gen_reference_ports(rows):
    """reference/ports ← compose 三檔 ports: 段全量表。

    只列 compose 實際存在的映射（留號決策語意歸 ADR 0019、不入表）；
    列序確定性＝來源檔→服務名→host port。
    """
    head = (f"{GEN_HEADER}\n# reference/ports — 全量正典表\n\n"
            f"來源＝{'＋'.join(COMPOSE_FILES)} 的 ports: 段（generate 重算；配號紀律歸 ADR 0019）。\n\n")
    if not rows:
        return head + "（compose 無任何 host port 映射）\n"
    lines = "\n".join(
        f"| {svc} | {host} | {cont} | {ip} | {src} |"
        for src, svc, host, cont, ip in
        sorted(rows, key=lambda r: (r[0], r[1], int(r[2]), int(r[3]))))
    return (head + "| 服務 | host port | 容器內 port | 綁定 IP | 來源檔 |\n"
            "|---|---|---|---|---|\n" + lines + "\n")


# ---------------------------------------------------------------------------
# routes 直解：rust-api/server/src/router.rs 的 `pub const ROUTES` 全量表（B-001）。
# 比照上方 ports 直解範式（窄假設行級解析＋fail-loud）；B-052「route 抽取防漏」關鍵——
# 寧可擋下、絕不靜默漏列一條 route。
# ---------------------------------------------------------------------------

ROUTER_SOURCE = "rust-api/server/src/router.rs"
# router.rs 全部合法 variant（掌握全集才能讓 fail-loud 準確、新增即紅逼同步）：
ROUTE_METHODS = {"Get": "GET", "Post": "POST", "Delete": "DELETE"}  # HttpMethod variant → casbin act 字面
ROUTE_PROTECTIONS = ("Public", "Authed", "Policy")   # Protection 三態
ROUTE_REQUIRED_FIELDS = ("path", "method", "case_key", "envelope_exception", "protection")

# 窄假設唯一合法項形（router.rs 現行實際使用的形；stripped 後 fullmatch）：
RE_ROUTES_CONST_OPEN = re.compile(r"^pub const ROUTES:\s*&\[RouteDef\]\s*=\s*&\[$")
RE_ROUTE_FIELD_PATH = re.compile(r'^path:\s*"([^"]*)",$')
RE_ROUTE_FIELD_METHOD = re.compile(r"^method:\s*HttpMethod::(\w+),$")
RE_ROUTE_FIELD_HANDLER = re.compile(r"^handler:\s*\|\|\s*(?:get|post|delete)\(.+\),$")
RE_ROUTE_FIELD_CASE_KEY = re.compile(r'^case_key:\s*"([^"]*)",$')
RE_ROUTE_FIELD_ENVELOPE = re.compile(r"^envelope_exception:\s*(true|false),$")
RE_ROUTE_FIELD_PROTECTION = re.compile(r"^protection:\s*Protection::(\w+),$")


class RouterRoutesError(Exception):
    """router.rs ROUTES 解析失敗（fail-loud：寧可擋下、不靜默漏列一條 route——B-052）。"""


def _parse_route_field(stripped, rel, n):
    """解析 RouteDef 條目內單行欄位。回 (key, value)；handler 識形後回 (None, None)（略過不入表）。

    不認得的欄／形／未知 method 或 protection variant → RouterRoutesError 指名 rel:行。
    """
    m = RE_ROUTE_FIELD_PATH.fullmatch(stripped)
    if m:
        return "path", m.group(1)
    m = RE_ROUTE_FIELD_CASE_KEY.fullmatch(stripped)
    if m:
        return "case_key", m.group(1)
    m = RE_ROUTE_FIELD_ENVELOPE.fullmatch(stripped)
    if m:
        return "envelope_exception", m.group(1) == "true"
    m = RE_ROUTE_FIELD_METHOD.fullmatch(stripped)
    if m:
        variant = m.group(1)
        if variant not in ROUTE_METHODS:
            raise RouterRoutesError(
                f"{rel}:行 {n}｜未知 HttpMethod::{variant}"
                f"（已知：{'／'.join(ROUTE_METHODS)}；router.rs 新增動詞請同步擴充本解析器）")
        return "method", ROUTE_METHODS[variant]
    m = RE_ROUTE_FIELD_PROTECTION.fullmatch(stripped)
    if m:
        variant = m.group(1)
        if variant not in ROUTE_PROTECTIONS:
            raise RouterRoutesError(
                f"{rel}:行 {n}｜未知 Protection::{variant}"
                f"（已知：{'／'.join(ROUTE_PROTECTIONS)}；router.rs 新增保護態請同步擴充本解析器）")
        return "protection", variant
    if RE_ROUTE_FIELD_HANDLER.fullmatch(stripped):
        return None, None  # handler 閉包：識形後略過不入表（form 變即 fail-loud）
    raise RouterRoutesError(
        f"{rel}:行 {n}｜RouteDef 內不認得的欄/形「{stripped}」"
        "（僅支援 path／method／handler／case_key／envelope_exception／protection；"
        "router.rs 改寫法請同步擴充本解析器）")


def parse_router_routes(text, rel):
    """解析 router.rs 的 `pub const ROUTES` block。
    回 [(path, method, protection, case_key, envelope_exception)]。

    行級窄假設解析（標準庫、不 parse Rust；只支援 router.rs 現行實際使用的形）：
    - 只解析 `pub const ROUTES: &[RouteDef] = &[` 起、`];` 止的那一段 block；其他 RouteDef
      出現處（struct 定義、build() 迭代、doc 註解）一律不碰。
    - block 內頂層只認 `RouteDef {` 起條目、`}`／`},` 收條目，空行／`//` 註解跳過；其餘 fail-loud。
    - 條目內每欄一行；handler 閉包識形後略過不入表；method／protection variant 必屬已知集。
    - 未知欄／重複欄／缺欄／未知 variant／找不到 ROUTES const／block 未收尾 → RouterRoutesError
      指名 rel:行——防來源改寫法時對照表靜默漏列（fail-loud 逼人同步擴充解析器）。
    """
    rows = []
    found_const, in_const, entry, entry_line = False, False, None, None
    for n, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not in_const:
            if RE_ROUTES_CONST_OPEN.fullmatch(stripped):
                found_const, in_const = True, True
            continue  # const 外一律忽略（含 struct 定義、build() 迭代、doc 註解）
        if not stripped or stripped.startswith("//"):
            continue  # 空行／註解行不終結區塊
        if entry is None:
            if stripped == "];":
                in_const = False
                break  # ROUTES const 收尾（唯一一段、無需續掃）
            if stripped == "RouteDef {":
                entry, entry_line = {}, n
                continue
            raise RouterRoutesError(
                f"{rel}:行 {n}｜ROUTES block 頂層不認得的行「{stripped}」"
                "（僅支援 RouteDef 條目與收尾 ];；router.rs 改寫法請同步擴充本解析器）")
        if stripped in ("}", "},"):
            missing = [f for f in ROUTE_REQUIRED_FIELDS if f not in entry]
            if missing:
                raise RouterRoutesError(
                    f"{rel}:行 {entry_line}｜RouteDef 條目缺欄 {missing}"
                    "（router.rs 改寫法請同步擴充本解析器）")
            rows.append((entry["path"], entry["method"], entry["protection"],
                         entry["case_key"], entry["envelope_exception"]))
            entry = None
            continue
        key, value = _parse_route_field(stripped, rel, n)
        if key is None:
            continue  # handler：略過
        if key in entry:
            raise RouterRoutesError(f"{rel}:行 {n}｜RouteDef 內重複欄「{key}」")
        entry[key] = value
    if not found_const:
        raise RouterRoutesError(
            f"{rel}｜找不到 `pub const ROUTES: &[RouteDef] = &[`——routes 對照表無法重算")
    if in_const:
        raise RouterRoutesError(f"{rel}｜ROUTES const block 未見收尾 ];（fail-loud、防半解析漏列）")
    return rows


def compute_router_rows(root):
    """讀 router.rs → parse_router_routes。回 rows；來源檔缺＝fail-loud。"""
    text = _read(root, ROUTER_SOURCE)
    if text is None:
        raise RouterRoutesError(f"{ROUTER_SOURCE}｜router 來源檔不存在——routes 對照表無法重算")
    return parse_router_routes(text, ROUTER_SOURCE)


def gen_reference_routes(rows):
    """reference/routes ← router.rs ROUTES const 全量表。

    只列 ROUTES 實際註冊的路由（handler 閉包不入表；授權語意歸 router.rs 文件）；
    列序確定性＝path→method。
    """
    head = (f"{GEN_HEADER}\n# reference/routes — 全量正典表\n\n"
            f"來源＝{ROUTER_SOURCE} 的 ROUTES const（generate 重算；handler 閉包不入表）。\n\n")
    if not rows:
        return head + "（ROUTES 無任何條目）\n"
    lines = "\n".join(
        f"| {path} | {method} | {protection} | {case_key} | {'是' if env else '否'} |"
        for path, method, protection, case_key, env in
        sorted(rows, key=lambda r: (r[0], r[1])))
    return (head + "| path | method | protection | case_key | envelope 例外 |\n"
            "|---|---|---|---|---|\n" + lines + "\n")


# ---------------------------------------------------------------------------
# screens 直解：base-web/src/router/elegant/routes.ts 的 generatedRoutes const 全量表（B-005）。
# 比照上方 routes 直解範式（窄假設行級解析＋fail-loud），惟來源含巢狀 children（深達 3 層）——
# 以「容器框堆疊」追蹤 array／route／meta 邊界、遞迴 flatten 全部 route。B-052「防漏」關鍵：
# 寧可擋下、絕不靜默漏列一條 screen。
# ---------------------------------------------------------------------------

ELEGANT_SOURCE = "base-web/src/router/elegant/routes.ts"
# route 物件合法頂層欄全集（掌握全集才能讓 fail-loud 準確、來源新增欄即紅逼同步）：
# name／path／component 抽值入表；props／redirect 識形後略過；meta／children 開子容器。
ELEGANT_ROUTE_SKIP_FIELDS = ("props", "redirect")
ELEGANT_ROUTE_REQUIRED_FIELDS = ("name", "path")   # 每條 route 物件必備（缺＝fail-loud）

# 窄假設唯一合法形（routes.ts 現行實際使用的形：單引號字串、elegant-router prettier-ignore
# 穩定格式；stripped 後 fullmatch）。其他寫法（雙引號、行內物件…）一律 fail-loud。
RE_ELEGANT_CONST_OPEN = re.compile(r"^export const generatedRoutes: GeneratedRoute\[\] = \[$")
RE_ELEGANT_NAME = re.compile(r"^name: '([^']*)',$")
RE_ELEGANT_PATH = re.compile(r"^path: '([^']*)',$")
RE_ELEGANT_COMPONENT = re.compile(r"^component: '([^']*)',$")
RE_ELEGANT_I18NKEY = re.compile(r"^i18nKey: '([^']*)',?$")
RE_ELEGANT_FIELD = {"name": RE_ELEGANT_NAME, "path": RE_ELEGANT_PATH,
                    "component": RE_ELEGANT_COMPONENT}


class ElegantRoutesError(Exception):
    """routes.ts generatedRoutes 解析失敗（fail-loud：寧可擋下、不靜默漏列一條 screen——B-052）。"""


def parse_elegant_routes(text, rel):
    """解析 routes.ts 的 `export const generatedRoutes` 陣列、flatten 全巢狀 route。
    回 [(name, path, component, i18nKey)]（每條 route 物件一列、含所有 children）。

    行級窄假設解析（標準庫、不 parse TS；只支援 routes.ts 現行實際使用的形）：
    - 只解析 `export const generatedRoutes: GeneratedRoute[] = [` 起、頂層 `];` 止的那一段；
      其他 import／型別／別處一律不碰。
    - 以容器框堆疊追蹤邊界：array（陣列，直屬子＝route 物件）／route（route 物件，欄集＝
      name/path/component/props/redirect/meta/children）／meta（只抽 i18nKey、其餘欄安全略過）。
      route 物件開＝裸 `{`；收＝`}`／`},`（收時即 flatten 入表，父／葉皆列）；children＝巢狀 array。
    - route 頂層見不認得的欄／形、重複欄、缺 name/path、找不到 const、陣列未收尾 → ElegantRoutesError
      指名 rel:行——防來源改寫法時對照表靜默漏列（fail-loud 逼人同步擴充解析器）。
    """
    rows = []
    stack = []                        # [(kind, entry)]；kind∈{array,route,meta}；entry＝route dict 或 None
    found_const = in_const = False
    for n, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not in_const:
            if RE_ELEGANT_CONST_OPEN.fullmatch(stripped):
                found_const = in_const = True
                stack.append(("array", None))
            continue                  # const 外一律忽略（import／型別／註解）
        if not stripped or stripped.startswith("//"):
            continue                  # 空行／註解行不終結區塊
        kind, entry = stack[-1]
        if kind == "meta":
            if stripped in ("}", "},"):
                stack.pop()           # meta 收尾（`}` 或 `},`）
                continue
            m = RE_ELEGANT_I18NKEY.fullmatch(stripped)
            if m:
                if "i18nKey" in entry:
                    raise ElegantRoutesError(f"{rel}:行 {n}｜meta 內重複 i18nKey")
                entry["i18nKey"] = m.group(1)
            continue                  # 其餘 meta 欄（title/icon/order/roles/…）安全略過、不 choke
        if kind == "array":
            if stripped == "{":
                stack.append(("route", {"_line": n}))
                continue
            if stripped in ("]", "],", "];"):
                stack.pop()
                if not stack:
                    in_const = False
                    break             # 頂層 generatedRoutes 陣列收尾（唯一一段、無需續掃）
                continue              # children 子陣列收尾
            raise ElegantRoutesError(
                f"{rel}:行 {n}｜陣列頂層不認得的行「{stripped}」"
                "（僅支援 route 物件 `{` 與收尾 `]`；routes.ts 改寫法請同步擴充本解析器）")
        # kind == "route"
        if stripped in ("}", "},"):
            missing = [f for f in ELEGANT_ROUTE_REQUIRED_FIELDS if f not in entry]
            if missing:
                raise ElegantRoutesError(
                    f"{rel}:行 {entry['_line']}｜route 物件缺欄 {missing}"
                    "（routes.ts 改寫法請同步擴充本解析器）")
            rows.append((entry["name"], entry["path"],
                         entry.get("component", ""), entry.get("i18nKey", "")))
            stack.pop()
            continue
        if stripped == "meta: {":
            stack.append(("meta", entry))     # meta 寫回同一 route entry（i18nKey 落此）
            continue
        if stripped == "children: [":
            stack.append(("array", None))     # 巢狀 children：遞迴進 array 框
            continue
        key = stripped.split(":", 1)[0].strip()
        if key in RE_ELEGANT_FIELD:
            m = RE_ELEGANT_FIELD[key].fullmatch(stripped)
            if not m:
                raise ElegantRoutesError(
                    f"{rel}:行 {n}｜route 欄「{key}」形不認得「{stripped}」"
                    "（僅支援單引號字串；routes.ts 改寫法請同步擴充本解析器）")
            if key in entry:
                raise ElegantRoutesError(f"{rel}:行 {n}｜route 物件內重複欄「{key}」")
            entry[key] = m.group(1)
            continue
        if key in ELEGANT_ROUTE_SKIP_FIELDS:
            continue                  # props／redirect：欄名已知、值不入表故不需驗形
        raise ElegantRoutesError(
            f"{rel}:行 {n}｜route 物件內不認得的欄/形「{stripped}」"
            "（僅支援 name／path／component／props／redirect／meta／children；"
            "routes.ts 改寫法請同步擴充本解析器）")
    if not found_const:
        raise ElegantRoutesError(
            f"{rel}｜找不到 `export const generatedRoutes: GeneratedRoute[] = [`——screens 對照表無法重算")
    if in_const:
        raise ElegantRoutesError(f"{rel}｜generatedRoutes 陣列未見收尾 ];（fail-loud、防半解析漏列）")
    return rows


def compute_screen_rows(root):
    """讀 routes.ts → parse_elegant_routes。回 rows；來源檔缺＝fail-loud。"""
    text = _read(root, ELEGANT_SOURCE)
    if text is None:
        raise ElegantRoutesError(f"{ELEGANT_SOURCE}｜elegant routes 來源檔不存在——screens 對照表無法重算")
    return parse_elegant_routes(text, ELEGANT_SOURCE)


def gen_reference_screens(rows):
    """reference/screens ← routes.ts generatedRoutes 全量表（全巢狀 route flatten）。

    每條 route 物件一列（父／葉皆入表）；列序確定性＝name（elegant-router name 全域唯一）。
    component／i18nKey 某 route 無則留「—」；path 內含 `|`（如 login module 選擇器）由 _md_cell 轉義。
    """
    head = (f"{GEN_HEADER}\n# reference/screens — 全量正典表\n\n"
            f"來源＝{ELEGANT_SOURCE} 的 generatedRoutes const"
            f"（generate 重算；全巢狀 route flatten、每條一列）。\n\n")
    if not rows:
        return head + "（generatedRoutes 無任何 route）\n"
    lines = "\n".join(
        f"| {_md_cell(name)} | {_md_cell(path)} | {_md_cell(component)} | {_md_cell(i18nKey)} |"
        for name, path, component, i18nKey in sorted(rows, key=lambda r: r[0]))
    return (head + "| name | path | component | i18nKey |\n"
            "|---|---|---|---|\n" + lines + "\n")


# ---------------------------------------------------------------------------
# backend 拒因字典鏈（B-007／FR-014、016-observability T019）：base-web locale 兩語
# `backend.*` 鍵樹（單一真相源、唯讀）→ ①reference/backend-msg-dict.md 對照表
# ②deploy 側 grafana text panel json（零 datasource）。比照 ports/routes 直解範式
# （窄假設行級解析＋fail-loud）；兩語鍵集不相等＝fail-loud（字典缺譯即紅、非靜默缺列）。
# ---------------------------------------------------------------------------

# backend 樹內唯二合法行形（stripped 後 fullmatch；註解行另行跳過）：
RE_DICT_OPEN = re.compile(r"^([A-Za-z_$][A-Za-z0-9_$]*):\s*\{$")
RE_DICT_LEAF = re.compile(
    r"^([A-Za-z_$][A-Za-z0-9_$]*):\s*(['\"`])((?:\\.|(?!\2).)*)\2,?$")
RE_DICT_ESCAPE = re.compile(r"\\(.)")


class BackendDictError(Exception):
    """locale backend 樹解析失敗（fail-loud：寧可擋下、不靜默漏一鍵或收殘值）。"""


def parse_locale_backend(text, rel):
    """自 locale TS 擷取頂層 backend: { … } 樹。回 {扁平鍵: 值}（鍵＝a.b.c）。

    窄假設：樹內每行恰為 註解（//…）／子樹開（key: {）／葉（key: '值',）／閉（} 或 },）
    之一；值同行閉合、三種引號皆收、跳脫以 \\x → x 還原；重複鍵＝fail-loud。
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.fullmatch(r"\s*backend:\s*\{", line):
            start = i
            break
    if start is None:
        raise BackendDictError(f"{rel}｜找不到頂層 backend: {{ 樹——字典無法重算")
    out, stack = {}, []
    for n, raw in enumerate(lines[start + 1:], start=start + 2):
        s = raw.strip()
        if not s or s.startswith("//"):
            continue
        m = RE_DICT_OPEN.fullmatch(s)
        if m:
            stack.append(m.group(1))
            continue
        m = RE_DICT_LEAF.fullmatch(s)
        if m:
            key = ".".join(stack + [m.group(1)])
            if key in out:
                raise BackendDictError(f"{rel}:行 {n}｜重複鍵 {key}")
            out[key] = RE_DICT_ESCAPE.sub(r"\1", m.group(3))
            continue
        if s in ("}", "},"):
            if not stack:
                if not out:
                    raise BackendDictError(f"{rel}｜backend 樹為空——字典無法重算")
                return out
            stack.pop()
            continue
        raise BackendDictError(f"{rel}:行 {n}｜backend 樹內無法解析的行形：{s[:80]}")
    raise BackendDictError(f"{rel}｜backend 樹未閉合（EOF）")


def compute_msg_dict_rows(root):
    """讀兩語 locale → 鍵集斷言相等 → 回 [(key, zh, en)]（鍵序確定性）。"""
    trees = []
    for lang, rel in MSG_DICT_LOCALES:
        text = _read(root, rel)
        if text is None:
            raise BackendDictError(f"{rel}｜locale 來源檔不存在——字典無法重算")
        trees.append(parse_locale_backend(text, rel))
    zh, en = trees
    if set(zh) != set(en):
        diff = "、".join(sorted(set(zh) ^ set(en)))
        raise BackendDictError(f"兩語 backend 鍵集不相等（缺譯即紅）：{diff}")
    return [(k, zh[k], en[k]) for k in sorted(zh)]


def _msg_dict_table(rows):
    return ("| key | zh-TW | en-US |\n|---|---|---|\n"
            + "\n".join(f"| {_md_cell(k)} | {_md_cell(z)} | {_md_cell(e)} |"
                        for k, z, e in rows) + "\n")


def gen_msg_dict_md(rows):
    """reference/backend-msg-dict ← locale backend.* 兩語對照表（D9 拍板＝兩語）。"""
    head = (f"{GEN_HEADER}\n# reference/backend-msg-dict — 拒因字典（機器生成）\n\n"
            f"來源＝{'＋'.join(rel for _, rel in MSG_DICT_LOCALES)} 之 backend.* 鍵樹"
            f"（generate 重算；B-007／FR-014、全鏈零手維）。\n\n")
    return head + _msg_dict_table(rows)


def gen_msg_dict_panel(rows):
    """deploy 側字典面板 json ← 同 rows（text panel markdown 嵌入、零 datasource）。"""
    dash = {
        "uid": "obs-backend-msg-dict",
        "title": "拒因字典 (backend-msg-dict)",
        "description": MSG_DICT_HINT,
        "tags": ["obs", "rev4-admin", "backend-msg-dict"],
        "schemaVersion": 39,
        "editable": False,
        "graphTooltip": 0,
        "time": {"from": "now-6h", "to": "now"},
        "refresh": "",
        "timezone": "browser",
        "templating": {"list": []},
        "annotations": {"list": []},
        "panels": [{
            "id": 1,
            "type": "text",
            "title": "backend.* 拒因鍵 → zh-TW／en-US 對照",
            "description": MSG_DICT_HINT,
            "gridPos": {"h": 30, "w": 24, "x": 0, "y": 0},
            "options": {"mode": "markdown", "code": {"language": "plaintext"},
                        "content": f"{MSG_DICT_HINT}\n\n{_msg_dict_table(rows)}"},
        }],
    }
    return json.dumps(dash, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------
# 快照管線：refresh（需 stack）→ reference-src 兩快照（契約 specs/002-schema-baseline/
# contracts/snapshot-reference.md §1）。generate／check 只讀快照、絕不碰 docker。
# ---------------------------------------------------------------------------

REFERENCE_SRC_DIR = "docs/ops/reference-src"
SCHEMA_SNAPSHOT = f"{REFERENCE_SRC_DIR}/schema-snapshot.json"
ACCOUNTS_SNAPSHOT = f"{REFERENCE_SRC_DIR}/accounts-snapshot.json"
ARCHETYPE_MAP = f"{REFERENCE_SRC_DIR}/archetype-map.json"
STACK_HINT = "docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait"
DB_USER = "soybean"
DB_NAME = "soybean_admin_rust"
COMPOSE_PSQL = ["docker", "compose", "-f", "docker-compose.yml",
                "-f", "docker-compose.dev.yml", "exec", "-T", "postgres"]

# 唯讀撈取（information_schema／pg_catalog／SELECT only）；每支包 json_agg 回單值 JSON。
# seaql_migrations 除外（框架表；build_* 再防禦性過濾一次）。
_JSON_WRAP = "SELECT COALESCE(json_agg(t), '[]'::json) FROM ({}) t"
SQL_COLUMNS = _JSON_WRAP.format(
    'SELECT c.table_name AS "table", c.column_name AS "column",'
    ' c.ordinal_position AS "ordinal", format_type(a.atttypid, a.atttypmod) AS "type",'
    " c.is_nullable = 'YES' AS \"nullable\", c.column_default AS \"default\""
    " FROM information_schema.columns c"
    " JOIN pg_class cl ON cl.relname = c.table_name"
    " JOIN pg_namespace ns ON ns.oid = cl.relnamespace AND ns.nspname = c.table_schema"
    " JOIN pg_attribute a ON a.attrelid = cl.oid AND a.attname = c.column_name"
    " WHERE c.table_schema = 'public' AND c.table_name <> 'seaql_migrations'"
    " ORDER BY c.table_name, c.ordinal_position")
SQL_INDEXES = _JSON_WRAP.format(
    'SELECT tablename AS "table", indexname AS "name", indexdef AS "definition"'
    " FROM pg_indexes WHERE schemaname = 'public' AND tablename <> 'seaql_migrations'"
    " ORDER BY tablename, indexname")
SQL_CONSTRAINTS = _JSON_WRAP.format(
    'SELECT rel.relname AS "table", con.conname AS "name",'
    ' pg_get_constraintdef(con.oid) AS "definition"'
    " FROM pg_constraint con"
    " JOIN pg_class rel ON rel.oid = con.conrelid"
    " JOIN pg_namespace ns ON ns.oid = rel.relnamespace"
    " WHERE ns.nspname = 'public' AND rel.relname <> 'seaql_migrations'"
    " ORDER BY rel.relname, con.conname")
# 帳號面三表；sys_user 明確逐欄 SELECT——絕不 SELECT *、password 欄不入快照（機密紀律）
SQL_USERS = _JSON_WRAP.format(
    "SELECT id, user_name, nick_name, status FROM sys_user ORDER BY id")
SQL_ROLES = _JSON_WRAP.format(
    "SELECT id, role_code, role_name, status FROM sys_role ORDER BY id")
SQL_BINDINGS = _JSON_WRAP.format(
    "SELECT user_id, role_id FROM sys_user_role ORDER BY user_id, role_id")

SCHEMA_COLUMN_KEYS = ("table", "column", "ordinal", "type", "nullable", "default")
SCHEMA_DEF_KEYS = ("table", "name", "definition")
USER_KEYS = ("id", "user_name", "nick_name", "status")
ROLE_KEYS = ("id", "role_code", "role_name", "status")
BINDING_KEYS = ("user_id", "role_id")


class SnapshotError(Exception):
    """快照管線失敗（stack 不在、撈取形不符、快照/歸屬檔缺）——fail-loud、絕不寫部分結果。"""


def _project(row, keys, what):
    """逐列投影到白名單欄集；多欄/缺欄＝fail-loud（多欄含 password 走私即機密紅線）。"""
    if not isinstance(row, dict):
        raise SnapshotError(f"{what} 列須為 object：{row!r}")
    extra = sorted(set(row) - set(keys))
    missing = [k for k in keys if k not in row]
    if extra or missing:
        raise SnapshotError(
            f"{what} 列欄集不符白名單（多：{extra or '無'}／缺：{missing or '無'}）"
            "——refresh 拒寫（撈取 SQL 與白名單須同步改）")
    return {k: row[k] for k in keys}


def _no_framework(rows):
    return [r for r in rows if r.get("table") != "seaql_migrations"]


def build_schema_snapshot(cols, idx, cons):
    """欄／索引／約束 → 確定性排序快照 dict（表名→ordinal；無產生時點欄位）。"""
    return {
        "columns": sorted((_project(r, SCHEMA_COLUMN_KEYS, "columns")
                           for r in _no_framework(cols)),
                          key=lambda r: (r["table"], r["ordinal"])),
        "indexes": sorted((_project(r, SCHEMA_DEF_KEYS, "indexes")
                           for r in _no_framework(idx)),
                          key=lambda r: (r["table"], r["name"])),
        "constraints": sorted((_project(r, SCHEMA_DEF_KEYS, "constraints")
                               for r in _no_framework(cons)),
                              key=lambda r: (r["table"], r["name"])),
    }


def build_accounts_snapshot(users, roles, bindings):
    """帳號面三表 → 確定性排序快照 dict；password 欄出現＝機密紅線 fail-loud。"""
    for u in users:
        if isinstance(u, dict) and "password" in u:
            raise SnapshotError(
                "機密紀律：sys_user 撈取含 password 欄——連雜湊值都不入快照，refresh 拒寫")
    return {
        "users": sorted((_project(u, USER_KEYS, "sys_user") for u in users),
                        key=lambda u: u["id"]),
        "roles": sorted((_project(r, ROLE_KEYS, "sys_role") for r in roles),
                        key=lambda r: r["id"]),
        "bindings": sorted((_project(b, BINDING_KEYS, "sys_user_role") for b in bindings),
                           key=lambda b: (b["user_id"], b["role_id"])),
    }


def snapshot_dumps(snap):
    """快照序列化：固定鍵序＋indent 2＋結尾換行——同輸入同 byte。"""
    return json.dumps(snap, ensure_ascii=False, indent=2) + "\n"


def _atomic_write(path, text):
    """原子替換寫檔（同目錄暫存→os.replace）；失敗不留半成品。"""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def psql_fetch(sql, root=None, run=subprocess.run):
    """compose exec psql 唯讀撈取、回 JSON rows；stack 不在＝fail-loud＋啟動提示。"""
    cmd = COMPOSE_PSQL + ["psql", "-U", DB_USER, "-d", DB_NAME,
                          "-v", "ON_ERROR_STOP=1", "-qAt", "-c", sql]
    try:
        proc = run(cmd, capture_output=True, text=True, cwd=root or ROOT)
    except OSError as ex:
        raise SnapshotError(
            f"無法執行 docker（{ex}）——refresh 需 dev stack 在跑；先啟動：{STACK_HINT}")
    if proc.returncode != 0:
        reason = (proc.stderr or proc.stdout).strip() or f"退出碼 {proc.returncode}"
        raise SnapshotError(
            f"psql 撈取失敗：{reason}——refresh 需 dev stack 在跑；先啟動：{STACK_HINT}")
    try:
        rows = json.loads(proc.stdout)
    except json.JSONDecodeError as ex:
        raise SnapshotError(f"psql 輸出非合法 JSON（{ex.msg}）——查詢形被改動？")
    if not isinstance(rows, list):
        raise SnapshotError("psql 輸出非 JSON array——查詢形被改動？")
    return rows


def cmd_refresh(root=None, fetch=psql_fetch):
    """refresh：六撈全數成功→組兩快照→原子替換落檔（絕不寫部分結果）。"""
    root = root or ROOT
    schema_text = snapshot_dumps(build_schema_snapshot(
        fetch(SQL_COLUMNS, root), fetch(SQL_INDEXES, root), fetch(SQL_CONSTRAINTS, root)))
    accounts_text = snapshot_dumps(build_accounts_snapshot(
        fetch(SQL_USERS, root), fetch(SQL_ROLES, root), fetch(SQL_BINDINGS, root)))
    for rel, text in ((SCHEMA_SNAPSHOT, schema_text), (ACCOUNTS_SNAPSHOT, accounts_text)):
        _atomic_write(os.path.join(root, rel), text)
        print(f"refresh：寫 {rel}（{_line_count(text)} 行）")
    return 0


def _load_reference_src(root, rel, hint):
    """讀 reference-src 追蹤檔；缺檔／壞 JSON＝fail-loud（轉真後即為表的存在前提）。"""
    text = _read(root, rel)
    if text is None:
        raise SnapshotError(f"{rel} 缺失——{hint}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as ex:
        raise SnapshotError(f"{rel} 非合法 JSON（{ex.msg}）——{hint}")


def gen_reference_schema(snap, archetypes):
    """reference/schema ← schema 快照＋archetype 歸屬。逐表分節（表名序）。

    archetypes＝{table: {"label": …, …}}；快照有表、map 無歸屬＝fail-loud 指名。
    """
    tables = sorted({r["table"] for key in ("columns", "indexes", "constraints")
                     for r in snap.get(key, [])})
    missing = [t for t in tables if t not in archetypes]
    if missing:
        raise SnapshotError(
            "archetype-map 缺表歸屬：" + "、".join(missing)
            + f"——先補 data-model §1 再登記 {ARCHETYPE_MAP}")
    unlabeled = [t for t in tables if not archetypes[t].get("label")]
    if unlabeled:
        raise SnapshotError(
            "archetype-map 條目缺 label：" + "、".join(unlabeled)
            + f"——補齊 {ARCHETYPE_MAP} 該表的 label 欄")
    head = (f"{GEN_HEADER}\n# reference/schema — 全量正典表\n\n"
            f"來源＝{SCHEMA_SNAPSHOT}（refresh 自實庫撈）＋{ARCHETYPE_MAP}（變體歸屬）；"
            "由 generate 重算。seaql_migrations 除外。\n")
    parts = [head]
    for table in tables:
        parts.append(f"\n## {table}（archetype {archetypes[table]['label']}）\n\n"
                     "| 欄 | 型別 | 可空 | 預設 |\n|---|---|---|---|\n")
        parts.append("".join(
            f"| {_md_cell(c['column'])} | {_md_cell(c['type'])} "
            f"| {'是' if c['nullable'] else '否'} | {_md_cell(c['default'])} |\n"
            for c in sorted((c for c in snap.get("columns", []) if c["table"] == table),
                            key=lambda c: c["ordinal"])))
        for label, key in (("索引", "indexes"), ("約束", "constraints")):
            rows = sorted((r for r in snap.get(key, []) if r["table"] == table),
                          key=lambda r: r["name"])
            if rows:
                parts.append(f"\n{label}：\n" + "".join(
                    f"- {r['name']}｜{r['definition']}\n" for r in rows))
    return "".join(parts)


def gen_reference_accounts(snap):
    """reference/accounts ← accounts 快照（帳號｜暱稱｜狀態｜角色綁定；零密碼欄）。"""
    role_code = {r["id"]: r["role_code"] for r in snap.get("roles", [])}
    bound = {}
    for b in snap.get("bindings", []):
        if b["role_id"] not in role_code:
            raise SnapshotError(
                f"accounts 快照綁定指向不存在的 role id {b['role_id']}"
                f"（user id {b['user_id']}）——重跑 tools/docs-sync.py refresh")
        bound.setdefault(b["user_id"], []).append(role_code[b["role_id"]])
    user_rows = "".join(
        f"| {_md_cell(u['user_name'])} | {_md_cell(u['nick_name'])} "
        f"| {_md_cell(u['status'])} | {_md_cell('、'.join(sorted(bound.get(u['id'], []))))} |\n"
        for u in snap.get("users", []))
    role_rows = "".join(
        f"| {_md_cell(r['role_code'])} | {_md_cell(r['role_name'])} "
        f"| {_md_cell(r['status'])} |\n"
        for r in snap.get("roles", []))
    return (f"{GEN_HEADER}\n# reference/accounts — 全量正典表\n\n"
            f"來源＝{ACCOUNTS_SNAPSHOT}（refresh 自實庫撈；零密碼欄——契約明文）；"
            "由 generate 重算。\n\n"
            "## 帳號\n\n| 帳號 | 暱稱 | 狀態 | 角色綁定 |\n|---|---|---|---|\n"
            + user_rows +
            "\n## 角色\n\n| 角色碼 | 角色名 | 狀態 |\n|---|---|---|\n" + role_rows)


def compute_snapshot_reference(root):
    """兩快照＋archetype-map → reference/{schema,accounts}.md。回 {rel: content}。"""
    refresh_hint = "先跑 tools/docs-sync.py refresh（需 dev stack 在跑）"
    schema_snap = _load_reference_src(root, SCHEMA_SNAPSHOT, refresh_hint)
    accounts_snap = _load_reference_src(root, ACCOUNTS_SNAPSHOT, refresh_hint)
    amap = _load_reference_src(
        root, ARCHETYPE_MAP, "追蹤中繼檔、隨 schema 刀維護（初始內容＝data-model §1 轉錄）")
    archetypes = {t["table"]: t for t in amap.get("tables", [])
                  if isinstance(t, dict) and "table" in t}
    return {
        f"{GENERATED_DIR}/reference/schema.md":
            gen_reference_schema(schema_snap, archetypes),
        f"{GENERATED_DIR}/reference/accounts.md":
            gen_reference_accounts(accounts_snap),
    }


def parse_events_loose(text):
    """generate 用的寬鬆解析（壞行、非 object 行跳過——擋壞行是 L3 的職責）。"""
    events = []
    for line in _jsonl_lines(text or ""):
        if line.strip():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(e, dict):
                events.append(e)
    return events


def compute_generated(root):
    """重算 docs/generated/ 全部應有內容。回 {rel: content}。"""
    events = parse_events_loose(_read(root, EVENTS))
    metas = [parse_front_matter(t)[0] for t in load_adrs(root).values()]
    btexts = [(_read(root, rel) or "") for rel in backlog_paths(root)]
    lessons_texts = [(_read(root, rel) or "") for rel in lessons_paths(root)]
    ctx = {
        "pins": index_pins(root),
        "constitution_version": constitution_version(root),
        "events": events,
        "adr_metas": metas,
        "backlog_count": len(RE_ENTRY["B"].findall(btexts[0])),
        "backlog_next": _parse_next("B", btexts[0]),
        "backlog_deferred_count": sum(len(RE_ENTRY["B"].findall(t)) for t in btexts[1:]),
        "lessons_count": sum(len(RE_ENTRY["L"].findall(t)) for t in lessons_texts),
        "lessons_next": _parse_next("L", lessons_texts[0]),
    }
    files = {
        f"{GENERATED_DIR}/STATE.md": gen_state(ctx),
        f"{GENERATED_DIR}/DECISIONS-INDEX.md": gen_decisions_index(metas),
    }
    files.update(gen_milestones(events))
    for name in REFERENCE_TABLES:
        if name in REFERENCE_LIVE:
            continue
        files[f"{GENERATED_DIR}/reference/{name}.md"] = gen_reference_stub(name)
    files[f"{GENERATED_DIR}/reference/ports.md"] = gen_reference_ports(compute_ports_rows(root))
    files[f"{GENERATED_DIR}/reference/routes.md"] = gen_reference_routes(compute_router_rows(root))
    files[f"{GENERATED_DIR}/reference/screens.md"] = gen_reference_screens(compute_screen_rows(root))
    msg_rows = compute_msg_dict_rows(root)
    files[MSG_DICT_MD] = gen_msg_dict_md(msg_rows)
    files[MSG_DICT_PANEL] = gen_msg_dict_panel(msg_rows)
    files.update(compute_snapshot_reference(root))
    return files


# ---------------------------------------------------------------------------
# L4 收刀事件存在性／L5 review 分流雙源對賬／L6 arch_impact 存在性＋最新刀雙向
# ---------------------------------------------------------------------------


def _norm_bid(s):
    """B-NNN 正規化為 3 位零填字串，令事件字串與 BACKLOG 條目可比。"""
    m = re.fullmatch(r"B-(\d+)", s) if isinstance(s, str) else None
    return f"B-{int(m.group(1)):03d}" if m else s


def _open_backlog_ids(root):
    """現況 BACKLOG 全卷（主檔＋滯後卷）仍開放的 B-NNN 條目集（RE_ENTRY 認真條目、
    非散文引用；滯後≠完成——滯後卷條目對 L4/L5 一律視為仍開放）。"""
    ids = set()
    for rel in backlog_paths(root):
        text = _read(root, rel) or ""
        ids.update(f"B-{int(m.group(1)):03d}" for m in RE_ENTRY["B"].finditer(text))
    return ids


def _backlog_id_ever_existed(root, nb):
    """B-NNN 是否曾在 BACKLOG.md git 史出現過（真被 defer、非 phantom/typo）。
    ★不問「何時加」：backlog 項或於 mid-feature commit、或於 merge 後之收刀簿記 commit 加入
    （CLAUDE.md §2 簿記排在 merge 之後），故 merge SHA 非可靠參考點——只問「有沒有真加過」。
    `｜` 為條目欄位分隔、散文引用不帶，故 `B-NNN｜` 專認真條目。git 不可用（測試）→False。"""
    out = git_out(["log", "--oneline", "-S", f"{nb}｜", "--", *backlog_paths(root)], root)
    return bool(out and out.strip())


def _backlog_done_ids(events):
    """曾在任一 feature_close／misc 之 backlog_done 被標記完成的 B-NNN 集（＝已被消化的證據；
    misc 通道＝輕量軌收刀、2026-07-17 調規）。"""
    out = set()
    for e in events:
        if e.get("type") in ("feature_close", "misc") and isinstance(e.get("backlog_done"), list):
            out.update(_norm_bid(b) for b in e["backlog_done"] if isinstance(b, str))
    return out


def _adr_ids_on_disk(root):
    """現況 ADR_DIR 下合法檔名的 4 碼 ADR 編號集。"""
    d = os.path.join(root, ADR_DIR)
    ids = set()
    if os.path.isdir(d):
        for n in os.listdir(d):
            m = RE_ADR_FILENAME.fullmatch(n)
            if m:
                ids.add(m.group(1))
    return ids


def lint_close_existence(root):
    """L4：逐 feature_close 驗其引用之 ADR／backlog／specs 目錄真實存在。回 findings。"""
    out = []
    events = parse_events_loose(_read(root, EVENTS))
    open_ids = _open_backlog_ids(root)
    done_ids = _backlog_done_ids(events)
    adr_ids = _adr_ids_on_disk(root)
    for e in events:
        etype = e.get("type")
        # misc 亦可攜 backlog_done（輕量軌消化通道、2026-07-17 調規）——同受「宣稱完成卻未刪列」檢查；
        # 其餘檢查（adrs/backlog_add/specs）對 misc 自然 no-op（欄不存在）。
        if etype not in ("feature_close", "misc"):
            continue
        feat = e.get("feature")
        where = f"{EVENTS}｜{feat if etype == 'feature_close' else 'misc ' + str(e.get('date'))}"
        for adr in e.get("adrs", []) or []:
            if adr not in adr_ids:
                out.append(finding(ERROR, "L4", where,
                                   f"adrs 引用 ADR {adr} 但 {ADR_DIR}/ 無對應檔"))
        for b in e.get("backlog_done", []) or []:
            if _norm_bid(b) in open_ids:
                out.append(finding(ERROR, "L4", where,
                                   f"backlog_done {b} 仍在 BACKLOG 卷（主檔或滯後卷；宣稱完成卻未刪列）"))
        for b in e.get("backlog_add", []) or []:
            nb = _norm_bid(b)
            # 快速路徑：現況仍開放 或 後續 backlog_done 消化＝顯然真被 defer、免 git。
            if nb in open_ids or nb in done_ids:
                continue
            # 事後獨立完成刪列（git 即史、不進 event）→查 BACKLOG git 史確認曾真加過；
            # 從未出現＝phantom/typo。git 不可用（測試無 git）→_ever_existed False→仍抓 phantom。
            if _backlog_id_ever_existed(root, nb):
                continue
            out.append(finding(ERROR, "L4", where,
                               f"backlog_add {b} 查無此項（BACKLOG git 史從未出現、疑 phantom/typo）"))
        if isinstance(feat, str) and not os.path.isdir(os.path.join(root, "specs", feat)):
            out.append(finding(ERROR, "L4", where, f"specs/{feat}/ 目錄不存在"))
    return out


def lint_review_existence(root):
    """L5：逐 review 驗分流引用（report 檔／to_backlog／wontfix_adr）真實存在。回 findings。"""
    out = []
    events = parse_events_loose(_read(root, EVENTS))
    open_ids = _open_backlog_ids(root)
    done_ids = _backlog_done_ids(events)
    adr_ids = _adr_ids_on_disk(root)
    tracked = set(tracked_files(root))
    for e in events:
        if e.get("type") != "review":
            continue
        where = f"{EVENTS}｜review {e.get('date')}"
        report = e.get("report")
        if isinstance(report, str):
            rel = f"docs/{report}"
            if not os.path.isfile(os.path.join(root, rel)) and rel not in tracked:
                out.append(finding(ERROR, "L5", where, f"report 檔不存在：{rel}"))
        fd = e.get("findings")
        if isinstance(fd, dict):
            for b in fd.get("to_backlog", []) or []:
                nb = _norm_bid(b)
                if nb not in open_ids and nb not in done_ids:
                    out.append(finding(ERROR, "L5", where,
                                       f"to_backlog {b} 查無此項（現況 BACKLOG 無、亦無後續 backlog_done 消化）"))
            for adr in fd.get("wontfix_adr", []) or []:
                if adr not in adr_ids:
                    out.append(finding(ERROR, "L5", where,
                                       f"wontfix_adr 引用 ADR {adr} 但 {ADR_DIR}/ 無對應檔"))
    return out


def _section_num(s):
    return int(s[1:]) if isinstance(s, str) and RE_SECTION.fullmatch(s) else None


def _arch_impact_nums(ai):
    """arch_impact 欄轉節號集；"none" 或非 list→空集（非 §N 項交 L3 驗形）。"""
    if not isinstance(ai, list):
        return set()
    return {n for n in (_section_num(s) for s in ai) if n is not None}


def _book_section_content(text):
    """活書各 §節內容（不含節標題行），供內容相異比對。回 {節號: 內容字串}。"""
    sec, buf, out = None, [], {}
    for line in (text or "").splitlines():
        m = RE_BOOK_SECTION.match(line)
        if m:
            if sec is not None:
                out[sec] = "\n".join(buf)
            sec, buf = int(m.group(1)), []
        elif sec is not None:
            buf.append(line)
    if sec is not None:
        out[sec] = "\n".join(buf)
    return out


def _arch_changed_sections(book_a, book_b):
    """兩版活書內容相異的 §節號集（含只存在於一版者）。"""
    sa, sb = _book_section_content(book_a), _book_section_content(book_b)
    return {n for n in set(sa) | set(sb) if sa.get(n) != sb.get(n)}


def lint_arch_impact(root):
    """L6：(a) 全 feature_close arch_impact §N 須為活書現存節；
    (b) 僅最新 feature_close：merge→簿記活書變動節集與 arch_impact 雙向相等。回 findings。

    (b) 現況側綁定該刀「簿記狀態」（非恆前進工作樹）：
      - 簿記尚未 commit（HEAD＝該刀 merge）＝pre-commit 閘時刻，as-built 僅在工作樹→讀工作樹；
      - 簿記已落地為 HEAD（HEAD^＝該刀 merge）→讀 HEAD 版活書（忽略工作樹後續漂移）；
      - HEAD 已前進超過簿記（下一支 feature 已 commit）或 SHA 取不到→跳過 (b)（fail-safe、不誤報）。
    綁定之必要：若恆讀工作樹，下一支 feature 的 mid-feature 活書編輯會被誤算進最新刀名下，
    產生無法滿足的假陽（下一支尚無 close event 可登記 arch_impact），全程硬擋 commit。
    歷史刀不做 (b)——其 merge 與現況簿記狀態無對應、慣例對不齊會誤報。
    """
    out = []
    events = parse_events_loose(_read(root, EVENTS))
    book = _read(root, BOOK)
    sec_set = set(book_section_lines(book)) if book is not None else set()
    closes = [e for e in events if e.get("type") == "feature_close"]
    # (a) 存在性：全 feature_close
    for e in closes:
        where = f"{EVENTS}｜{e.get('feature')}"
        for n in sorted(_arch_impact_nums(e.get("arch_impact"))):
            if n not in sec_set:
                out.append(finding(ERROR, "L6", where,
                                   f"arch_impact §{n} 非活書（{BOOK}）現存節"))
    # (b) 雙向：僅最新刀，且現況側綁定該刀簿記狀態（非恆前進工作樹）
    if closes:
        latest = closes[-1]
        where = f"{EVENTS}｜{latest.get('feature')}"
        m = latest.get("merge")
        m_sha = git_out(["rev-parse", "--verify", m], root) if isinstance(m, str) else None
        head = git_out(["rev-parse", "--verify", "HEAD"], root)
        head_par = git_out(["rev-parse", "--verify", "HEAD^"], root)
        book_m = git_out(["show", f"{m}:{BOOK}"], root) if isinstance(m, str) else None
        book_now = None
        if m_sha is not None and head is not None and m_sha.strip() == head.strip():
            # State 1：pre-commit 簿記（HEAD＝merge、as-built 尚未落地、僅在工作樹）→ 讀工作樹
            book_now = book
        elif m_sha is not None and head_par is not None and m_sha.strip() == head_par.strip():
            # State 2：簿記已落地為 HEAD（HEAD^＝merge）→ 讀 HEAD 版活書、忽略工作樹後續漂移
            book_now = head_file(BOOK, root)
        # 否則 HEAD 已前進超過簿記／SHA 取不到 → book_now=None → 跳過 (b)（fail-safe）
        if book_m is not None and book_now is not None:
            claimed = _arch_impact_nums(latest.get("arch_impact"))
            changed = _arch_changed_sections(book_m, book_now)
            for n in sorted(claimed - changed):
                out.append(finding(ERROR, "L6", where,
                                   f"最新刀宣稱 arch_impact §{n} 但 merge→簿記活書該節無實際變動"))
            for n in sorted(changed - claimed):
                out.append(finding(ERROR, "L6", where,
                                   f"最新刀簿記活書 §{n} 內容有變動但 arch_impact 未宣稱"))
    return out


def tracked_blobs(root):
    """tracked 檔清單扣掉 gitlink（160000）條目——憑證掃描的外層面（data-model §2）。"""
    rels = []
    for line in (git_out(["ls-files", "-s"], root) or "").splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path and parts and parts[0] != "160000":
            rels.append(path)
    return rels


def _cred_read_text(path):
    """回 (全文, 意外跳過原因)。

    二進位（前 8KB 含 NUL）＝刻意 skip（R2：憑證必為文字），回 (None, None)；讀不到
    （缺席／目錄／權限）＝意外，回 (None, 原因)——呼叫端必須留信號，「沒掃到」靜默
    當成乾淨即 fail-open。
    """
    try:
        with open(path, "rb") as fh:
            probe = fh.read(CRED_BINARY_PROBE)
            if b"\x00" in probe:
                return None, None
            return (probe + fh.read()).decode("utf-8", errors="replace"), None
    except OSError as exc:
        return None, f"讀取失敗（{exc.__class__.__name__}）"


def _cred_staged_added(root):
    """staged 新增行（index vs HEAD）過樣式集；回 [(rel, label)]。

    ★判定面不得只有工作樹快照：閘要護的是「這次要進版控的內容」。實證兩態——`git add`
    後把工作樹檔 rm、或 `git add` 後把工作樹版本洗白——工作樹都是乾淨的、index blob 卻
    仍帶憑證。改讀全 index blob 語意最純但實測 414 blob 走 `cat-file` 需 2.2s（工作樹讀
    僅 1.3s），故只補「本次新增內容」這條增量：成本正比 staged 變更量，與 FR-008 同哲學。
    """
    diff = git_out(["diff", "--cached", "-U0"], root)
    return cred_diff_hits(diff) if diff else []


def lint_cred_outer(root):
    """L16 外層面：全 tracked 文字檔過樣式集（data-model §2 第 1 列）＋staged 新增行補掃。

    兩面聯集去重（同一 rel×label 只報一次；工作樹面帶行號、優先）。
    """
    out, seen = [], set()
    for rel in tracked_blobs(root):
        if rel in CRED_WHITELIST:
            continue
        text, unread = _cred_read_text(os.path.join(root, rel))
        if unread:
            out.append(finding(WARN, "L16", rel,
                               f"工作樹{unread}——該檔工作樹面未掃、非判定為乾淨"
                               "（staged 內容另由 index 面補掃）"))
        if text is None:
            continue
        for label, n in scan_cred_text(text):
            if (rel, label) in seen:
                continue
            seen.add((rel, label))
            out.append(finding(ERROR, "L16", f"{rel}:行 {n}",
                               f"憑證內容命中（label={label}）——移除內容並輪替該憑證；"
                               "無 inline 豁免，確需豁免走 CRED_WHITELIST＋ADR（0077）"))
    for rel, label in _cred_staged_added(root):
        if rel in CRED_WHITELIST or (rel, label) in seen:
            continue
        seen.add((rel, label))
        out.append(finding(ERROR, "L16", f"{rel}:staged",
                           f"staged 內容憑證命中（label={label}）——工作樹版本已無此內容、"
                           "但 index 這份即將進版控；移除並輪替後重新 git add"))
    return out


def _cred_index_gitlink(root, sub):
    for line in (git_out(["ls-files", "-s", "--", sub], root) or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "160000":
            return parts[1]
    return None


def _cred_grep_tree(subdir, tree):
    """退化全樹掃：逐樣式 `git grep -nE -e <樣式> <tree>`；回 (命中清單, 失敗說明或 None)。

    ★`-e` 不可省：樣式集含以連字號開頭者（PEM 頭），省略時 git 會把樣式當成未知選項、
    以退出碼 129 中止，「非零＝零命中」的寫法即把它吞成乾淨＝fail-open。
    ★`-I` 不可省：二進位檔命中時 git 改輸出「Binary file <tree>:<path> matches」——該行
    逐冒號切欄後路徑欄變成「<path> matches」殘餘文字（指名一個不存在的檔），且與外層面
    「前 8KB 含 NUL 即 skip」的二進位規則（R2）不一致。統一以 `-I` 跳過二進位。
    ★退出碼三分而非二分：0＝有命中、1＝確無命中、其餘（129 引數錯、128 物件不在該庫……）
    ＝掃描根本沒跑成，一律回失敗說明給呼叫端升 ERROR——退化面的語意是 fail-closed 向完整掃，
    把執行失敗解讀成乾淨會做出比不掃更危險的假保證（FR-008）。
    """
    out = []
    for label, pat in CRED_PATTERNS:
        try:
            r = subprocess.run(["git", "-c", "core.quotepath=off", "grep", "-nEI",
                                "-e", pat.pattern, tree], cwd=subdir,
                               capture_output=True, encoding="utf-8", errors="replace")
        except OSError as exc:
            return out, f"樣式 {label} 之 git grep 無法執行（{exc.__class__.__name__}）"
        if r.returncode not in (0, 1):
            head = ((r.stderr or "").strip().splitlines() or [""])[0]
            return out, (f"樣式 {label} 之 git grep 退出碼 {r.returncode}"
                         + (f"：{head}" if head else ""))
        for line in r.stdout.splitlines():
            parts = line.split(":", 3)          # <tree>:<path>:<行號>:<內容>
            if len(parts) >= 2 and (parts[1], label) not in out:
                out.append((parts[1], label))
    return out, None


def lint_cred_submodules(root):
    """L16 增量面：staged 含 gitlink 變動時掃 old..new 新增行（R3；data-model §2 第 2/3 列）。"""
    out = []
    staged = set((git_out(["diff", "--cached", "--name-only"], root) or "").splitlines())
    for sub in CRED_SUBMODULES:
        if sub not in staged:
            continue
        subdir = os.path.join(root, sub)
        if not os.path.exists(os.path.join(subdir, ".git")):
            out.append(finding(WARN, "L16", sub,
                               "submodule worktree 缺席——憑證增量掃跳過（唯讀看碼模式）"))
            continue
        new = _cred_index_gitlink(root, sub)
        if new is None:
            out.append(finding(WARN, "L16", sub,
                               "staged gitlink SHA 讀不到——憑證增量掃跳過"))
            continue
        old = (git_out(["rev-parse", f"HEAD:{sub}"], root) or "").strip()
        diff = git_out(["diff", old, new, "-U0"], subdir) if old else None
        if diff is None:
            out.append(finding(WARN, "L16", sub,
                               f"舊 pin（{old[:12] or '無'}）不可解或 diff 失敗——"
                               "退化為新 pin 全樹掃描（fail-closed 向完整掃）"))
            hits, err = _cred_grep_tree(subdir, new)
            if err:
                out.append(finding(ERROR, "L16", sub,
                                   f"退化全樹掃執行失敗（{err}）——掃描面未建立、不得視同乾淨；"
                                   "補齊該 pin 物件（回該庫 fetch）後重跑"))
        else:
            hits = cred_diff_hits(diff)
        for path, label in hits:
            out.append(finding(ERROR, "L16", f"{sub}/{path}",
                               f"submodule 新進內容憑證命中（label={label}）——"
                               "回該庫移除並輪替後重 bump pin"))
    return out


def lint_credentials(root):
    """L16 組裝：self-test 防恆綠＋外層全量＋submodule 增量（contracts G1）。"""
    return cred_self_test() + lint_cred_outer(root) + lint_cred_submodules(root)


def run_lint(root):
    """組裝 L3～L16（含 L4/L5/L6 收刀完整性閘、L16 憑證掃描）全套。回 findings。
    git 不可用＝fail-closed 單發 ERROR。"""
    if not git_available(root):
        return [finding(ERROR, "L1", ".",
                        "git 不可用——HEAD 基線與掃描語料無法建立，lint fail-closed（修復 git 後重跑）")]
    findings = []
    findings += lint_events(_read(root, EVENTS) or "")
    findings += lint_close_existence(root)
    findings += lint_review_existence(root)
    findings += lint_arch_impact(root)
    findings += lint_budgets(root)
    amend = os.environ.get("DOCS_SYNC_ADR_AMEND") == "1"
    findings += lint_adrs(load_adrs(root), load_head_adrs(root), amend=amend)
    bpaths = backlog_paths(root)
    findings += lint_ids("B", [(_read(root, p) or "") for p in bpaths],
                         [head_file(p, root) for p in bpaths])
    lpaths = lessons_paths(root)
    findings += lint_ids("L", [(_read(root, p) or "") for p in lpaths],
                         [head_file(p, root) for p in lpaths])
    book = _read(root, BOOK)
    if book is not None:
        findings += lint_tense(book)
    findings += lint_dictionary(
        {rel: _read(root, rel) for rel in (BOOK, "CLAUDE.md")
         if _read(root, rel) is not None})
    # G4 引用健康：L12~L15 同一語料＝全 tracked md 扣史料豁免（specs/、reviews/ 都在內）
    tracked = tracked_files(root)
    md_texts = {rel: _read(root, rel) or ""
                for rel in tracked if rel.endswith(".md") and not _is_exempt(rel)}
    untracked = [l for l in (git_out(["ls-files", "--others", "--exclude-standard"], root)
                             or "").splitlines() if l]
    findings += lint_links(md_texts, set(tracked) | set(untracked))
    findings += lint_line_refs(md_texts)
    findings += lint_volatile_deep_links(md_texts)
    findings += lint_memory_refs(md_texts)
    findings += lint_credentials(root)
    return findings


def print_findings(findings):
    for f in findings:
        print(f"[{f['level']}] {f['code']}｜{f['where']}｜{f['msg']}")


def book_section_lines(book_text):
    """活書各節行數（§3.2 更新契約 3：每 commit 輸出各節行數表）。"""
    sec, count, counts = None, 0, {}
    for line in book_text.splitlines():
        m = RE_BOOK_SECTION.match(line)
        if m:
            if sec is not None:
                counts[sec] = count
            sec, count = int(m.group(1)), 0
        elif sec is not None:
            count += 1
    if sec is not None:
        counts[sec] = count
    return counts


def cmd_lint():
    findings = run_lint(ROOT)
    print_findings(findings)
    book = _read(ROOT, BOOK)
    if book is not None:
        cells = [f"§{s} {n}/{SECTION_QUOTAS.get(s, '—')}"
                 for s, n in sorted(book_section_lines(book).items())]
        print("活書各節行數：" + "｜".join(cells))
    errors = [f for f in findings if f["level"] == ERROR]
    print(f"lint：{len(errors)} 錯誤／{len(findings) - len(errors)} 警告")
    return 1 if errors else 0


def cmd_generate():
    if not git_available(ROOT):
        print("[ERROR] git 不可用——pins 等 git 來源無法讀取，generate 中止（fail-closed）",
              file=sys.stderr)
        return 1
    adrs = load_adrs(ROOT)
    for fn, text in sorted(backfill_supersessions(adrs).items()):
        path = os.path.join(ROOT, ADR_DIR, fn)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"回填 supersedes 對稱欄：{ADR_DIR}/{fn}")
    files = compute_generated(ROOT)
    for rel, content in sorted(files.items()):
        path = os.path.join(ROOT, rel)
        if rel == MSG_DICT_PANEL:
            # grafana provider 每 30s 掃描該目錄——原子替換防讀到半成品（T003 staging 紀律）
            _atomic_write(path, content)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    # generated/ 全域歸生成器管轄：非生成物一律移除（含 .gitkeep）
    gen_root = os.path.join(ROOT, GENERATED_DIR)
    for dirpath, _, names in os.walk(gen_root):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, "/")
            if rel not in files:
                os.remove(os.path.join(dirpath, name))
                print(f"移除非生成物：{rel}")
    print(f"generate：重算 {len(files)} 檔完成")
    return 0


def cmd_check():
    if not git_available(ROOT):
        print("[ERROR] git 不可用——check 無法建立比對基線，fail-closed", file=sys.stderr)
        return 1
    findings = check_generated(ROOT, compute_generated(ROOT))
    pending = backfill_supersessions(load_adrs(ROOT))
    for fn in sorted(pending):
        findings.append(finding(ERROR, "L1", f"{ADR_DIR}/{fn}",
                                "supersedes 對稱回填待跑（tools/docs-sync.py generate）"))
    for rel in unstaged_generated(ROOT):
        findings.append(finding(ERROR, "L1", rel,
                                "生成物有未 staged 變更（跑了 generate 忘了 git add——"
                                "staged 內容過期，入版即漂移）"))
    print_findings(findings)
    print(f"check：{'不一致 ' + str(len(findings)) + ' 處' if findings else '一致'}")
    return 1 if findings else 0


def cmd_errata(keyword):
    texts = {}
    for rel in tracked_files(ROOT):
        try:
            text = _read(ROOT, rel)
        except (UnicodeDecodeError, OSError):
            continue
        if text is not None:
            texts[rel] = text
    hits = errata_scan(texts, keyword)
    for rel, n, line in hits:
        print(f"{rel}:行 {n}｜{line.strip()}")
    print(f"errata「{keyword}」：{len(hits)} 處命中（逐處處置、勿只修被點名那一處）")
    return 0


# ---------------------------------------------------------------------------
# 自帶測試
# ---------------------------------------------------------------------------

VALID_CLOSE = {
    "type": "feature_close", "feature": "001-system-settings",
    "merge": "abc1234", "date": "2026-07-10", "summary": "打樣刀收刀",
    "pins": {"web": "deadbee", "api": "cafe123"}, "adrs": ["0007"],
    "arch_impact": ["§6"], "backlog_add": [], "backlog_done": ["B-003"],
}
VALID_MISC = {"type": "misc", "date": "2026-07-02", "summary": "bootstrap 完成"}
VALID_REVIEW = {
    "type": "review", "date": "2026-08-01", "scope": "001-005 cumulative",
    "report": "reviews/20260801-cumulative.md",
    "findings": {"total": 3, "fixed": 1, "to_backlog": ["B-009"], "wontfix_adr": ["0012"]},
}


def _jl(*objs):
    return "".join(json.dumps(o, ensure_ascii=False) + "\n" for o in objs)


ADR_OK_A = (
    "---\nid: \"0001\"\ntitle: 甲決策\ndate: 2026-07-05\nstatus: superseded\n"
    "supersedes: []\nsuperseded_by: [0002]\n---\n\n## 背景\n舊案。\n"
)
ADR_OK_B = (
    "---\nid: \"0002\"\ntitle: 乙決策\ndate: 2026-07-08\nstatus: accepted\n"
    "supersedes: [0001]\nsuperseded_by: []\n---\n\n## 背景\n新案。\n"
)


class TestLintAdrs(unittest.TestCase):
    def test_symmetric_pair_passes(self):
        adrs = {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}
        self.assertEqual(lint_adrs(adrs, dict(adrs)), [])

    def test_missing_required_field(self):
        bad = "---\nid: \"0003\"\ndate: 2026-07-05\nstatus: draft\n---\nbody\n"
        f = lint_adrs({"0003-x.md": bad}, {})
        self.assertTrue(any("title" in x["msg"] for x in f))

    def test_bad_status(self):
        bad = ADR_OK_B.replace("status: accepted", "status: done")
        f = lint_adrs({"0002-new.md": bad}, {})
        self.assertTrue(any("status" in x["msg"] for x in f))

    def test_id_filename_mismatch(self):
        f = lint_adrs({"0009-new.md": ADR_OK_B}, {})
        self.assertTrue(any("檔名" in x["msg"] for x in f))

    def test_bad_filename(self):
        f = lint_adrs({"2-new.md": ADR_OK_B.replace('id: "0002"', 'id: "2"')}, {})
        self.assertTrue(any("檔名" in x["msg"] for x in f))

    def test_supersedes_asymmetry(self):
        a = ADR_OK_A.replace("superseded_by: [0002]", "superseded_by: []")
        f = lint_adrs({"0001-old.md": a, "0002-new.md": ADR_OK_B}, {})
        self.assertTrue(any("對稱" in x["msg"] for x in f))

    def test_supersedes_dangling_target(self):
        f = lint_adrs({"0002-new.md": ADR_OK_B}, {})
        self.assertTrue(any("0001" in x["msg"] for x in f))

    def test_superseded_status_required(self):
        a = ADR_OK_A.replace("status: superseded", "status: accepted")
        f = lint_adrs({"0001-old.md": a, "0002-new.md": ADR_OK_B}, {})
        self.assertTrue(any("superseded" in x["msg"] for x in f))

    def test_accepted_body_immutable(self):
        cur = ADR_OK_B.replace("新案。", "偷偷改寫。")
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": cur},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B})
        self.assertEqual(len(f), 1)
        self.assertIn("不可變", f[0]["msg"])

    def test_accepted_body_amend_escape(self):
        cur = ADR_OK_B.replace("新案。", "修個錯字。")
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": cur},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}, amend=True)
        self.assertEqual(f, [])

    def test_tool_backfill_of_superseded_by_allowed(self):
        head_b = ADR_OK_B.replace("superseded_by: []", "")  # HEAD 版尚無該欄
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": head_b})
        self.assertEqual(f, [])

    def test_deletion_banned(self):
        f = lint_adrs({"0002-new.md": ADR_OK_B.replace("supersedes: [0001]", "supersedes: []")},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B})
        self.assertTrue(any("刪除" in x["msg"] for x in f))

    def test_draft_freely_editable(self):
        head = ADR_OK_B.replace("status: accepted", "status: draft")
        cur = head.replace("新案。", "改來改去。")
        f = lint_adrs({"0002-new.md": cur.replace("supersedes: [0001]", "supersedes: []")},
                      {"0002-new.md": head.replace("supersedes: [0001]", "supersedes: []")})
        self.assertEqual(f, [])


BACKLOG_V1 = "<!-- next: B-003 -->\n# BACKLOG\n\n- B-001｜甲\n- B-002｜乙\n"


class TestLintIds(unittest.TestCase):
    def test_clean_passes(self):
        self.assertEqual(lint_ids("B", [BACKLOG_V1], [BACKLOG_V1]), [])

    def test_duplicate_id(self):
        cur = BACKLOG_V1 + "- B-002｜丙\n"
        f = lint_ids("B", [cur], [BACKLOG_V1])
        self.assertTrue(any("重複" in x["msg"] for x in f))

    def test_id_beyond_next(self):
        cur = BACKLOG_V1 + "- B-007｜丙\n"
        f = lint_ids("B", [cur], [BACKLOG_V1])
        self.assertTrue(any("next" in x["msg"] for x in f))

    def test_next_must_not_decrease(self):
        cur = BACKLOG_V1.replace("B-003 ", "B-002 ").replace("- B-002｜乙\n", "")
        f = lint_ids("B", [cur], [BACKLOG_V1])
        self.assertTrue(any("單調" in x["msg"] for x in f))

    def test_new_id_must_take_fresh_number(self):
        head = "<!-- next: B-005 -->\n# BACKLOG\n\n- B-004｜丁\n"
        cur = head + "- B-002｜回收舊號\n"   # B-002 曾用過已刪
        f = lint_ids("B", [cur], [head])
        self.assertTrue(any("回收" in x["msg"] for x in f))

    def test_new_entry_bumps_next(self):
        cur = BACKLOG_V1.replace("B-003 ", "B-004 ") + "- B-003｜丙\n"
        self.assertEqual(lint_ids("B", [cur], [BACKLOG_V1]), [])

    def test_missing_header(self):
        f = lint_ids("B", ["# BACKLOG\n- B-001｜甲\n"], [BACKLOG_V1])
        self.assertTrue(any("next" in x["msg"] for x in f))

    def test_lessons_multi_volume_duplicate(self):
        main = "<!-- next: L-103 -->\n# LESSONS\n- **L-102**｜新坑\n"
        vol = "# LESSONS-001-101\n- **L-001**｜舊坑\n- **L-102**｜撞號\n"
        f = lint_ids("L", [main, vol], [main, vol])
        self.assertTrue(any("重複" in x["msg"] for x in f))

    def test_repairing_midline_entry_not_recycle(self):
        # B-106 場景：HEAD 端條目黏他行行尾（非行首、嚴格 RE_ENTRY 不認），staged 補換行
        # 修復不得誤判舊號回收——反回收 HEAD 豁免視野採寬鬆子串形（｜為欄位分隔、散文引用不帶）
        head = "<!-- next: B-005 -->\n# BACKLOG\n\n- B-003｜甲（註）- B-004｜乙\n"
        cur = head.replace("（註）- B-004｜乙", "（註）\n- B-004｜乙")
        self.assertEqual(lint_ids("B", [cur], [head]), [])

    def test_backlog_multi_volume_move_and_duplicate(self):
        # 滯後卷與主檔同視野：同 commit 整行搬移＝非舊號回收；跨卷撞號可偵測
        head_main = "<!-- next: B-005 -->\n# BACKLOG\n\n- B-003｜甲\n- B-004｜乙\n"
        cur_main = head_main.replace("- B-003｜甲\n", "")
        vol = "# BACKLOG-DEFERRED — 滯後卷\n\n- B-003｜甲｜★滯後：release 前\n"
        self.assertEqual(lint_ids("B", [cur_main, vol], [head_main, None]), [])
        dup = vol + "- B-004｜乙撞號\n"
        f = lint_ids("B", [cur_main, dup], [head_main, None])
        self.assertTrue(any("重複" in x["msg"] for x in f))

    def test_lessons_plain_form_same_view(self):
        # B-105：plain 形（- L-NNN｜）與粗體形同視野——計數入帳、
        # 反回收兩側同視（plain→粗體正規化不得誤判舊號回收）、跨形撞號可偵測
        head = "<!-- next: L-103 -->\n# LESSONS\n- **L-101**｜甲\n- L-102｜乙\n"
        self.assertEqual(len(RE_ENTRY["L"].findall(head)), 2)
        cur = head.replace("- L-102｜", "- **L-102**｜")
        self.assertEqual(lint_ids("L", [cur], [head]), [])
        dup = head + "- **L-102**｜跨形撞號\n"
        f = lint_ids("L", [dup], [head])
        self.assertTrue(any("重複" in x["msg"] for x in f))


class TestGenMilestones(unittest.TestCase):
    def test_empty(self):
        files = gen_milestones([])
        self.assertEqual(list(files), ["docs/generated/MILESTONES.md"])
        self.assertIn("（尚無事件）", files["docs/generated/MILESTONES.md"])

    def test_rows_and_header(self):
        files = gen_milestones([VALID_MISC, VALID_CLOSE])
        text = files["docs/generated/MILESTONES.md"]
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertIn("001-system-settings", text)
        self.assertIn("bootstrap 完成", text)

    def test_year_split(self):
        old = dict(VALID_MISC); old["date"] = "2025-12-31"
        files = gen_milestones([old, VALID_MISC])
        self.assertIn("docs/generated/MILESTONES-2025.md", files)
        self.assertIn("docs/generated/MILESTONES.md", files)
        self.assertNotIn("2025-12-31", files["docs/generated/MILESTONES.md"])


class TestGenDecisionsIndex(unittest.TestCase):
    def test_empty(self):
        self.assertIn("（尚無 ADR）", gen_decisions_index([]))

    def test_sorted_by_id(self):
        metas = [parse_front_matter(ADR_OK_B)[0], parse_front_matter(ADR_OK_A)[0]]
        text = gen_decisions_index(metas)
        self.assertLess(text.index("0001"), text.index("0002"))
        self.assertIn("superseded", text)


class TestGenState(unittest.TestCase):
    CTX = {
        "pins": {"web": "deadbeef00", "api": None},
        "constitution_version": None,
        "events": [VALID_MISC, VALID_MISC, VALID_MISC, VALID_CLOSE],
        "adr_metas": [],
        "backlog_count": 2, "backlog_next": 6, "backlog_deferred_count": 2,
        "lessons_count": 101, "lessons_next": 102,
    }

    def test_contains_core_blocks(self):
        text = gen_state(self.CTX)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertIn("deadbee", text)          # pin 短 SHA
        self.assertIn("未建置", text)            # api pin 缺
        self.assertIn("未鑄", text)              # constitution 版本缺
        self.assertIn("B-006", text)            # backlog next
        self.assertIn("滯後：2", text)           # 滯後卷分計
        self.assertIn("101", text)              # lessons count

    def test_tail_three_events_newest_first(self):
        text = gen_state(self.CTX)
        self.assertIn("001-system-settings", text)   # 最新一筆（feature_close）
        self.assertEqual(text.count("bootstrap 完成"), 2)  # 尾 3 筆只含 2 筆 misc

    def test_within_budget(self):
        self.assertLessEqual(token_count(gen_state(self.CTX)), 4000)


class TestBackfill(unittest.TestCase):
    def test_backfill_superseded_by_and_status(self):
        a_head = ADR_OK_A.replace("superseded_by: [0002]", "superseded_by: []") \
                          .replace("status: superseded", "status: accepted")
        changed = backfill_supersessions({"0001-old.md": a_head, "0002-new.md": ADR_OK_B})
        self.assertEqual(list(changed), ["0001-old.md"])
        meta, body = parse_front_matter(changed["0001-old.md"])
        self.assertEqual(meta["superseded_by"], ["0002"])
        self.assertEqual(meta["status"], "superseded")
        self.assertEqual(body, parse_front_matter(a_head)[1])  # body 一字不動

    def test_noop_when_symmetric(self):
        self.assertEqual(
            backfill_supersessions({"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}), {})


class TestErrata(unittest.TestCase):
    def test_hits_case_insensitive(self):
        hits = errata_scan({"a.md": "有 Port 設定\n無關行\n", "b.md": "PORT 又見\n"}, "port")
        self.assertEqual([(h[0], h[1]) for h in hits], [("a.md", 1), ("b.md", 1)])

    def test_no_hits(self):
        self.assertEqual(errata_scan({"a.md": "x\n"}, "沒有"), [])


class TestCheckGenerated(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs/generated/reference"))
        self.computed = {
            "docs/generated/STATE.md": "內容A\n",
            "docs/generated/reference/ports.md": "stub\n",
        }
        for rel, content in self.computed.items():
            with open(os.path.join(self.root, rel), "w", encoding="utf-8") as fh:
                fh.write(content)

    def tearDown(self):
        self.tmp.cleanup()

    def test_in_sync(self):
        self.assertEqual(check_generated(self.root, self.computed), [])

    def test_drift_detected(self):
        with open(os.path.join(self.root, "docs/generated/STATE.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("被手改\n")
        f = check_generated(self.root, self.computed)
        self.assertEqual(len(f), 1)
        self.assertIn("STATE.md", f[0]["where"])

    def test_missing_file(self):
        os.remove(os.path.join(self.root, "docs/generated/reference/ports.md"))
        f = check_generated(self.root, self.computed)
        self.assertEqual(len(f), 1)

    def test_extra_file(self):
        with open(os.path.join(self.root, "docs/generated/EXTRA.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("手加\n")
        f = check_generated(self.root, self.computed)
        self.assertEqual(len(f), 1)
        self.assertIn("EXTRA", f[0]["where"])


COMPOSE_PORTS_SAMPLE = (
    "# 註解\n"
    "name: demo\n"
    "services:\n"
    "  front-nginx:\n"
    "    ports:\n"
    '      - "127.0.0.1:42080:80"\n'
    '      - "127.0.0.1:42443:443"\n'
    "    volumes:\n"
    "      - ./x:/x:ro\n"
    "  postgres:\n"
    "    ports:\n"
    '      - "127.0.0.1:45432:5432"\n'
    "volumes:\n"
    "  x:\n"
)


class TestComposePorts(unittest.TestCase):
    def test_parse_short_syntax(self):
        rows = parse_compose_ports(COMPOSE_PORTS_SAMPLE, "docker-compose.dev.yml")
        self.assertEqual(rows, [
            ("front-nginx", "42080", "80", "127.0.0.1"),
            ("front-nginx", "42443", "443", "127.0.0.1"),
            ("postgres", "45432", "5432", "127.0.0.1"),
        ])

    def test_no_ports_section(self):
        self.assertEqual(parse_compose_ports("services:\n  a:\n    image: x\n", "f.yml"), [])

    def test_item_at_same_indent_as_ports_key(self):
        # 回歸（quality review）：同縮排清單項（YAML 合法形）曾被靜默漏列
        text = ("services:\n"
                "  a:\n"
                "    ports:\n"
                '    - "127.0.0.1:9999:80"\n'
                "    volumes:\n"
                "    - ./x:/x\n")
        self.assertEqual(parse_compose_ports(text, "f.yml"),
                         [("a", "9999", "80", "127.0.0.1")])

    def test_bad_item_at_same_indent_still_fails_loud(self):
        text = 'services:\n  a:\n    ports:\n    - "0.0.0.0:1:2"\n'
        with self.assertRaises(ComposePortsError) as cm:
            parse_compose_ports(text, "f.yml")
        self.assertIn("行 4", str(cm.exception))

    def test_unknown_item_fails_loud_with_file_and_line(self):
        for bad in ("- 127.0.0.1:1:2",      # 無引號
                    '- "0.0.0.0:1:2"',      # 非 127.0.0.1 綁定
                    "- target: 80",          # 長語法
                    '- "8080:80"'):          # 無綁定 IP 前綴
            text = f"services:\n  a:\n    ports:\n      {bad}\n"
            with self.assertRaises(ComposePortsError, msg=bad) as cm:
                parse_compose_ports(text, "f.yml")
            self.assertIn("f.yml", str(cm.exception), msg=bad)
            self.assertIn("行 4", str(cm.exception), msg=bad)

    def test_unexpected_ports_key_shape_fails_loud(self):
        with self.assertRaises(ComposePortsError):   # inline value
            parse_compose_ports("services:\n  a:\n    ports: []\n", "f.yml")
        with self.assertRaises(ComposePortsError):   # 非服務直屬（深一層）
            parse_compose_ports("services:\n  a:\n    x:\n      ports:\n", "f.yml")

    def test_unknown_service_line_fails_loud(self):
        # 不擋則 service 殘留前值→後續 ports 錯掛到前一個服務（靜默錯列）
        for bad in ("b:  # 行內註解", '"b":', "b: {}"):
            text = f'services:\n  a:\n    ports:\n      - "127.0.0.1:1:1"\n  {bad}\n'
            with self.assertRaises(ComposePortsError, msg=bad) as cm:
                parse_compose_ports(text, "f.yml")
            self.assertIn("f.yml", str(cm.exception), msg=bad)
            self.assertIn("行 5", str(cm.exception), msg=bad)

    def test_compute_ports_rows_missing_source_fails_loud(self):
        with tempfile.TemporaryDirectory() as root:
            for rel in COMPOSE_FILES[:-1]:
                with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                    fh.write("services:\n")
            with self.assertRaises(ComposePortsError) as cm:
                compute_ports_rows(root)
            self.assertIn(COMPOSE_FILES[-1], str(cm.exception))

    def test_gen_reference_ports_sorted_and_deterministic(self):
        rows = [("docker-compose.example.yml", "example-dev", "42089", "80", "127.0.0.1"),
                ("docker-compose.dev.yml", "front-nginx", "42443", "443", "127.0.0.1"),
                ("docker-compose.dev.yml", "front-nginx", "42080", "80", "127.0.0.1")]
        text = gen_reference_ports(rows)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("42080"), text.index("42443"))   # host port 序
        self.assertLess(text.index("42443"), text.index("42089"))   # 來源檔序
        self.assertEqual(text, gen_reference_ports(list(reversed(rows))))  # 入序無關

    def test_gen_reference_ports_empty(self):
        self.assertIn("無任何 host port 映射", gen_reference_ports([]))

    def test_state_ports_line_is_live_not_stub(self):
        text = gen_state(TestGenState.CTX)
        for line in text.splitlines():
            if line.startswith("- reference/ports"):
                self.assertNotIn("stub", line)
                self.assertIn("generate", line)
                break
        else:
            self.fail("STATE 缺 reference/ports 對賬行")

    def test_check_reports_ports_drift_as_l2(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs/generated/reference"))
            rel = "docs/generated/reference/ports.md"
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("舊表\n")
            f = check_generated(root, {rel: "新表\n"})
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["code"], "L2")
            self.assertIn("ports", f[0]["msg"])


# 單條乾淨 RouteDef 欄集（fail-loud 案例逐行代換其一）
ROUTER_CLEAN_FIELDS = (
    '        path: "/health",\n'
    "        method: HttpMethod::Get,\n"
    "        handler: || get(health_ok),\n"
    '        case_key: "health",\n'
    "        envelope_exception: true,\n"
    "        protection: Protection::Public,\n"
)
# 完整樣本：const 前置 struct 定義＋block 內註解＋build() 迭代（皆須被忽略、不誤抓）
ROUTER_ROUTES_SAMPLE = (
    "use axum::Router;\n"
    "pub struct RouteDef {\n"                     # ← const 外的 RouteDef 字樣：須忽略
    "    pub path: &'static str,\n"               # ← 看似 path 欄、但不在 const：須忽略
    "}\n"
    "pub const ROUTES: &[RouteDef] = &[\n"
    + ROUTER_CLEAN_FIELDS.join(("    RouteDef {\n", "    },\n"))
    + "    // block 內註解：須跳過、不終結區塊\n"
    "    RouteDef {\n"
    '        path: "/auth/login",\n'
    "        method: HttpMethod::Post,\n"
    "        handler: || post(crate::handler::auth::login),\n"
    '        case_key: "auth-login",\n'
    "        envelope_exception: false,\n"
    "        protection: Protection::Policy,\n"
    "    },\n"
    "];\n"
    "pub fn build() {\n"
    "    for def in ROUTES {}\n"                   # ← const 外的 ROUTES 字樣：須忽略
    "}\n"
)


def _router_one(fields):
    """把單條欄集包成完整 ROUTES const 文字（fail-loud 案例用）。"""
    return ("pub const ROUTES: &[RouteDef] = &[\n"
            "    RouteDef {\n" + fields + "    },\n"
            "];\n")


class TestRouterRoutes(unittest.TestCase):
    def test_parse_clean_sample(self):
        rows = parse_router_routes(ROUTER_ROUTES_SAMPLE, "router.rs")
        # 恰 2 條（struct 定義／build() 迭代未被誤抓）；handler 不入表、method 已映射字面
        self.assertEqual(rows, [
            ("/health", "GET", "Public", "health", True),
            ("/auth/login", "POST", "Policy", "auth-login", False),
        ])

    def test_parse_real_router_rs(self):
        rows = compute_router_rows(ROOT)
        self.assertGreater(len(rows), 0, "真實 router.rs 應解析出 route")
        health = [r for r in rows if r[0] == "/health"]
        self.assertEqual(len(health), 1, "應含且僅含一條 /health")
        self.assertEqual(health[0][1], "GET")
        self.assertTrue(health[0][4], "/health 應標 envelope 例外")

    def test_unknown_method_variant_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS.replace("HttpMethod::Get", "HttpMethod::Patch")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("Patch", str(cm.exception))
        self.assertIn("行 4", str(cm.exception))

    def test_unknown_protection_variant_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS.replace("Protection::Public", "Protection::Admin")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("Admin", str(cm.exception))

    def test_unknown_field_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS + "        weight: 5,\n"
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("f.rs", str(cm.exception))

    def test_malformed_path_shape_fails_loud(self):
        # path 無引號＝不認得的形（窄假設：必引號短語法）
        bad = ROUTER_CLEAN_FIELDS.replace('path: "/health",', "path: /health,")
        with self.assertRaises(RouterRoutesError):
            parse_router_routes(_router_one(bad), "f.rs")

    def test_handler_shape_change_fails_loud(self):
        # handler 非 get()／post()／delete() 閉包＝不認得的形（不盲跳過；探針改 patch——
        # delete 已為合法形、008 U7 寫端五端點）
        bad = ROUTER_CLEAN_FIELDS.replace(
            "handler: || get(health_ok),", "handler: || patch(health_ok),")
        with self.assertRaises(RouterRoutesError):
            parse_router_routes(_router_one(bad), "f.rs")

    def test_duplicate_field_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS + '        path: "/dup",\n'
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("重複", str(cm.exception))

    def test_missing_field_fails_loud(self):
        bad = ROUTER_CLEAN_FIELDS.replace(
            "        protection: Protection::Public,\n", "")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(_router_one(bad), "f.rs")
        self.assertIn("protection", str(cm.exception))

    def test_top_level_junk_in_block_fails_loud(self):
        text = ("pub const ROUTES: &[RouteDef] = &[\n"
                "    surprise_line,\n"
                "];\n")
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(text, "f.rs")
        self.assertIn("行 2", str(cm.exception))

    def test_missing_const_fails_loud(self):
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes("fn main() {}\n", "f.rs")
        self.assertIn("ROUTES", str(cm.exception))

    def test_unterminated_block_fails_loud(self):
        text = "pub const ROUTES: &[RouteDef] = &[\n    RouteDef {\n" + ROUTER_CLEAN_FIELDS
        with self.assertRaises(RouterRoutesError) as cm:
            parse_router_routes(text, "f.rs")
        self.assertIn("收尾", str(cm.exception))

    def test_compute_router_rows_missing_source_fails_loud(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(RouterRoutesError) as cm:
                compute_router_rows(root)
            self.assertIn(ROUTER_SOURCE, str(cm.exception))

    def test_gen_reference_routes_sorted_and_deterministic(self):
        rows = [("/b", "GET", "Authed", "b", False),
                ("/a", "POST", "Public", "a-post", False),
                ("/a", "GET", "Public", "a-get", True)]
        text = gen_reference_routes(rows)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("/a | GET"), text.index("/a | POST"))  # 同 path→method 序
        self.assertLess(text.index("/a | POST"), text.index("/b | GET"))  # path 序
        self.assertEqual(text, gen_reference_routes(list(reversed(rows))))  # 入序無關
        self.assertIn("| 是 |", text)  # envelope True→是
        self.assertIn("| 否 |", text)  # envelope False→否

    def test_gen_reference_routes_empty(self):
        self.assertIn("無任何條目", gen_reference_routes([]))

    def test_state_routes_line_is_live_not_stub(self):
        text = gen_state(TestGenState.CTX)
        for line in text.splitlines():
            if line.startswith("- reference/routes"):
                self.assertNotIn("stub", line)
                self.assertIn("generate", line)
                break
        else:
            self.fail("STATE 缺 reference/routes 對賬行")

    def test_check_reports_routes_drift_as_l2(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs/generated/reference"))
            rel = "docs/generated/reference/routes.md"
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("舊表\n")
            f = check_generated(root, {rel: "新表\n"})
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["code"], "L2")
            self.assertIn("routes", f[0]["msg"])


# 單條乾淨 route 欄集（fail-loud 案例逐行代換其一；i18nKey 為 meta 內末欄、無尾逗號）
ELEGANT_CLEAN_FIELDS = (
    "    name: 'demo',\n"
    "    path: '/demo',\n"
    "    component: 'view.demo',\n"
    "    meta: {\n"
    "      title: 'demo',\n"
    "      i18nKey: 'route.demo'\n"
    "    }\n"
)
# 完整巢狀樣本：含父 route（有／無 component）＋深達 3 層 children＋meta 雜欄（roles/localIcon…）；
# const 外的 import／型別字樣須被忽略、不誤抓。
ELEGANT_ROUTES_SAMPLE = (
    "import type { GeneratedRoute } from '@elegant-router/types';\n"
    "export const generatedRoutes: GeneratedRoute[] = [\n"
    "  {\n"
    "    name: '403',\n"
    "    path: '/403',\n"
    "    component: 'layout.blank$view.403',\n"
    "    meta: {\n"
    "      title: '403',\n"
    "      i18nKey: 'route.403',\n"
    "      constant: true,\n"
    "      hideInMenu: true\n"
    "    }\n"
    "  },\n"
    "  {\n"
    "    name: 'alova',\n"
    "    path: '/alova',\n"
    "    component: 'layout.base',\n"
    "    meta: {\n"
    "      title: 'alova',\n"
    "      i18nKey: 'route.alova',\n"
    "      icon: 'carbon:http',\n"
    "      order: 7,\n"
    "      roles: ['R_SUPER']\n"
    "    },\n"
    "    children: [\n"
    "      {\n"
    "        name: 'alova_request',\n"
    "        path: '/alova/request',\n"
    "        component: 'view.alova_request',\n"
    "        meta: {\n"
    "          title: 'alova_request',\n"
    "          i18nKey: 'route.alova_request',\n"
    "          order: 1\n"
    "        }\n"
    "      }\n"
    "    ]\n"
    "  },\n"
    "  {\n"
    "    name: 'multi-menu_second',\n"
    "    path: '/multi-menu/second',\n"
    "    meta: {\n"
    "      title: 'multi-menu_second',\n"
    "      i18nKey: 'route.multi-menu_second',\n"
    "      order: 2\n"
    "    },\n"
    "    children: [\n"
    "      {\n"
    "        name: 'multi-menu_second_child',\n"
    "        path: '/multi-menu/second/child',\n"
    "        meta: {\n"
    "          title: 'multi-menu_second_child',\n"
    "          i18nKey: 'route.multi-menu_second_child'\n"
    "        },\n"
    "        children: [\n"
    "          {\n"
    "            name: 'multi-menu_second_child_home',\n"
    "            path: '/multi-menu/second/child/home',\n"
    "            component: 'view.multi-menu_second_child_home',\n"
    "            meta: {\n"
    "              title: 'multi-menu_second_child_home',\n"
    "              i18nKey: 'route.multi-menu_second_child_home'\n"
    "            }\n"
    "          }\n"
    "        ]\n"
    "      }\n"
    "    ]\n"
    "  }\n"
    "];\n"
)


def _elegant_one(fields):
    """把單條欄集包成完整 generatedRoutes const 文字（fail-loud 案例用）。"""
    return ("export const generatedRoutes: GeneratedRoute[] = [\n"
            "  {\n" + fields + "  }\n"
            "];\n")


class TestElegantRoutes(unittest.TestCase):
    def test_parse_clean_nested_sample(self):
        rows = parse_elegant_routes(ELEGANT_ROUTES_SAMPLE, "routes.ts")
        # 6 條 route 物件（父＋葉全 flatten）：403／alova／alova_request／
        # multi-menu_second／multi-menu_second_child／multi-menu_second_child_home
        self.assertEqual(len(rows), 6)
        d = {r[0]: r for r in rows}
        self.assertEqual(d["403"],
                         ("403", "/403", "layout.blank$view.403", "route.403"))
        # 深層巢狀（3 層）child 確有入表
        self.assertEqual(d["multi-menu_second_child_home"],
                         ("multi-menu_second_child_home", "/multi-menu/second/child/home",
                          "view.multi-menu_second_child_home", "route.multi-menu_second_child_home"))
        # 父 route 無 component → 空字串（gen 時轉 —）；i18nKey 仍抽到
        self.assertEqual(d["multi-menu_second"][2], "")
        self.assertEqual(d["multi-menu_second"][3], "route.multi-menu_second")

    def test_meta_extra_fields_do_not_choke(self):
        # meta 內 roles 陣列／icon／order 等雜欄安全略過、不致 fail-loud
        rows = parse_elegant_routes(ELEGANT_ROUTES_SAMPLE, "routes.ts")
        alova = [r for r in rows if r[0] == "alova"][0]
        self.assertEqual(alova, ("alova", "/alova", "layout.base", "route.alova"))

    def test_parse_real_routes_ts(self):
        rows = compute_screen_rows(ROOT)
        self.assertGreater(len(rows), 0, "真實 routes.ts 應解析出 route")
        names = [r[0] for r in rows]
        self.assertIn("403", names)
        # 深層巢狀（3 層）route 確有 flatten 入表
        self.assertIn("multi-menu_second_child_home", names)
        self.assertEqual(len(names), len(set(names)), "elegant-router name 應全域唯一")
        # rows 數＝來源檔 route 物件總數（每條 route 恰一 name: 行）
        src = _read(ROOT, ELEGANT_SOURCE)
        self.assertEqual(len(rows), len(re.findall(r"(?m)^\s*name: '", src)))

    def test_unknown_top_level_field_fails_loud(self):
        bad = ELEGANT_CLEAN_FIELDS + "    surprise: 1,\n"
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(_elegant_one(bad), "f.ts")
        self.assertIn("f.ts", str(cm.exception))
        self.assertIn("surprise", str(cm.exception))

    def test_malformed_name_shape_fails_loud(self):
        # name 無引號＝不認得的形（窄假設：必單引號短語法）
        bad = ELEGANT_CLEAN_FIELDS.replace("name: 'demo',", "name: demo,")
        with self.assertRaises(ElegantRoutesError):
            parse_elegant_routes(_elegant_one(bad), "f.ts")

    def test_duplicate_field_fails_loud(self):
        bad = ELEGANT_CLEAN_FIELDS + "    name: 'dup',\n"
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(_elegant_one(bad), "f.ts")
        self.assertIn("重複", str(cm.exception))

    def test_missing_required_field_fails_loud(self):
        bad = ELEGANT_CLEAN_FIELDS.replace("    path: '/demo',\n", "")
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(_elegant_one(bad), "f.ts")
        self.assertIn("path", str(cm.exception))

    def test_top_level_junk_in_array_fails_loud(self):
        text = ("export const generatedRoutes: GeneratedRoute[] = [\n"
                "  surprise,\n"
                "];\n")
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(text, "f.ts")
        self.assertIn("行 2", str(cm.exception))

    def test_missing_const_fails_loud(self):
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes("const x = 1;\n", "f.ts")
        self.assertIn("generatedRoutes", str(cm.exception))

    def test_unterminated_array_fails_loud(self):
        text = ("export const generatedRoutes: GeneratedRoute[] = [\n"
                "  {\n" + ELEGANT_CLEAN_FIELDS + "  }\n")   # 缺頂層收尾 ];
        with self.assertRaises(ElegantRoutesError) as cm:
            parse_elegant_routes(text, "f.ts")
        self.assertIn("收尾", str(cm.exception))

    def test_compute_screen_rows_missing_source_fails_loud(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ElegantRoutesError) as cm:
                compute_screen_rows(root)
            self.assertIn(ELEGANT_SOURCE, str(cm.exception))

    def test_gen_reference_screens_sorted_and_deterministic(self):
        rows = [("bravo", "/b", "view.b", "route.b"),
                ("alpha", "/a", "", "route.a"),
                ("charlie", "/c", "view.c", "")]
        text = gen_reference_screens(rows)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("alpha"), text.index("bravo"))    # name 序
        self.assertLess(text.index("bravo"), text.index("charlie"))
        self.assertEqual(text, gen_reference_screens(list(reversed(rows))))  # 入序無關
        self.assertIn("| alpha | /a | — | route.a |", text)          # 空 component→—
        self.assertIn("| charlie | /c | view.c | — |", text)         # 空 i18nKey→—

    def test_gen_reference_screens_escapes_pipe_in_path(self):
        # login path 內含 module 選擇器 `|`——須轉義否則破表格欄
        rows = [("login", "/login/:module(pwd-login|code-login)?",
                 "layout.blank$view.login", "route.login")]
        text = gen_reference_screens(rows)
        self.assertIn(r"pwd-login\|code-login", text)

    def test_gen_reference_screens_empty(self):
        self.assertIn("無任何 route", gen_reference_screens([]))

    def test_state_screens_line_is_live_not_stub(self):
        text = gen_state(TestGenState.CTX)
        for line in text.splitlines():
            if line.startswith("- reference/screens"):
                self.assertNotIn("stub", line)
                self.assertIn("generate", line)
                break
        else:
            self.fail("STATE 缺 reference/screens 對賬行")

    def test_check_reports_screens_drift_as_l2(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "docs/generated/reference"))
            rel = "docs/generated/reference/screens.md"
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write("舊表\n")
            f = check_generated(root, {rel: "新表\n"})
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["code"], "L2")
            self.assertIn("screens", f[0]["msg"])


MSG_DICT_TS_SAMPLE = (
    "const local: App.I18n.Schema = {\n"
    "  backend: {\n"
    "    common: {\n"
    "      // 行內註解（跳過）\n"
    "      listSeparator: '、',\n"
    "      success: '操作成功'\n"
    "    },\n"
    "    biz: {\n"
    "      user: {\n"
    "        inUse: '掛有 {userCount} 個使用者',\n"
    "        quoted: \"雙引號值\",\n"
    "        ticked: `反引號值`,\n"
    "        escaped: 'It\\'s ok'\n"
    "      }\n"
    "    }\n"
    "  },\n"
    "  system: {\n"
    "    title: 'not-backend'\n"
    "  }\n"
    "};\n"
)


class TestBackendMsgDict(unittest.TestCase):
    def test_parse_normal_nested(self):
        d = parse_locale_backend(MSG_DICT_TS_SAMPLE, "f.ts")
        self.assertEqual(d, {
            "common.listSeparator": "、",
            "common.success": "操作成功",
            "biz.user.inUse": "掛有 {userCount} 個使用者",
            "biz.user.quoted": "雙引號值",
            "biz.user.ticked": "反引號值",
            "biz.user.escaped": "It's ok",
        })

    def test_missing_backend_fails(self):
        with self.assertRaises(BackendDictError) as cm:
            parse_locale_backend("const local = {\n  other: {}\n};\n", "f.ts")
        self.assertIn("backend", str(cm.exception))

    def test_bad_line_fails_with_file_and_line(self):
        for bad in ("key: unquoted,",        # 無引號值
                    "key: ['a'],",           # 陣列值
                    "key: '跨行未閉",         # 值未閉合
                    "'quoted-key': 'v',"):   # 引號鍵（backend 樹現無、窄假設擋下）
            text = f"  backend: {{\n    {bad}\n  }},\n"
            with self.assertRaises(BackendDictError, msg=bad) as cm:
                parse_locale_backend(text, "f.ts")
            self.assertIn("f.ts:行 2", str(cm.exception), msg=bad)

    def test_unclosed_tree_fails(self):
        with self.assertRaises(BackendDictError) as cm:
            parse_locale_backend("  backend: {\n    a: {\n      b: 'v'\n", "f.ts")
        self.assertIn("未閉合", str(cm.exception))

    def test_duplicate_key_fails(self):
        text = "  backend: {\n    a: 'x',\n    a: 'y'\n  },\n"
        with self.assertRaises(BackendDictError) as cm:
            parse_locale_backend(text, "f.ts")
        self.assertIn("重複鍵 a", str(cm.exception))

    def test_empty_tree_fails(self):
        with self.assertRaises(BackendDictError):
            parse_locale_backend("  backend: {\n  },\n", "f.ts")

    def _root_with_locales(self, zh, en):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = os.path.join(tmp.name, "base-web/src/locales/langs")
        os.makedirs(d)
        for name, text in (("zh-tw.ts", zh), ("en-us.ts", en)):
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        return tmp.name

    def test_compute_rows_two_locales(self):
        root = self._root_with_locales(
            "  backend: {\n    auth: {\n      failed: '帳密錯誤'\n    }\n  },\n",
            "  backend: {\n    auth: {\n      failed: 'Bad credentials'\n    }\n  },\n")
        self.assertEqual(compute_msg_dict_rows(root),
                         [("auth.failed", "帳密錯誤", "Bad credentials")])

    def test_keyset_mismatch_fails(self):
        root = self._root_with_locales(
            "  backend: {\n    a: 'x'\n  },\n",
            "  backend: {\n    b: 'y'\n  },\n")
        with self.assertRaises(BackendDictError) as cm:
            compute_msg_dict_rows(root)
        self.assertIn("鍵集不相等", str(cm.exception))
        self.assertIn("a", str(cm.exception))

    def test_missing_locale_file_fails(self):
        root = self._root_with_locales("  backend: {\n    a: 'x'\n  },\n", "")
        os.remove(os.path.join(root, "base-web/src/locales/langs/en-us.ts"))
        with self.assertRaises(BackendDictError) as cm:
            compute_msg_dict_rows(root)
        self.assertIn("en-us.ts", str(cm.exception))

    def test_gen_md_form(self):
        md = gen_msg_dict_md([("auth.failed", "帳密|錯誤", "Bad credentials")])
        self.assertTrue(md.startswith(GEN_HEADER))
        self.assertIn("| auth.failed | 帳密\\|錯誤 | Bad credentials |", md)

    def test_gen_panel_form(self):
        text = gen_msg_dict_panel([("auth.failed", "帳密錯誤", "Bad credentials")])
        dash = json.loads(text)
        self.assertEqual(dash["uid"], "obs-backend-msg-dict")
        self.assertNotIn("datasource", text)         # 零 datasource
        self.assertIn("嚴禁手改", dash["description"])  # 檔頭 hint
        panel = dash["panels"][0]
        self.assertEqual(panel["type"], "text")
        self.assertIn("auth.failed", panel["options"]["content"])
        self.assertIn("帳密錯誤", panel["options"]["content"])

    def test_check_intercepts_tampered_panel(self):
        # 手改攔截形：deploy 側面板被手改一字元 → check 紅（L2 指名來源）
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = tmp.name
        os.makedirs(os.path.join(root, GENERATED_DIR))
        panel_path = os.path.join(root, MSG_DICT_PANEL)
        os.makedirs(os.path.dirname(panel_path))
        good = gen_msg_dict_panel([("a", "甲", "A")])
        computed = {MSG_DICT_PANEL: good}
        with open(panel_path, "w", encoding="utf-8") as fh:
            fh.write(good)
        self.assertEqual(check_generated(root, computed), [])   # 一致＝綠
        with open(panel_path, "w", encoding="utf-8") as fh:
            fh.write(good.replace("甲", "乙", 1))               # 手改一字元
        f = check_generated(root, computed)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["code"], "L2")
        self.assertIn("backend-msg-dict.json", f[0]["where"])

    def test_check_missing_panel_reported(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = tmp.name
        os.makedirs(os.path.join(root, GENERATED_DIR))
        f = check_generated(root, {MSG_DICT_PANEL: "x"})
        self.assertEqual(len(f), 1)
        self.assertIn("缺生成檔", f[0]["msg"])


class TestLintLinks(unittest.TestCase):
    PATHS = {"docs/ops/BACKLOG.md", "docs/arc42/ARCHITECTURE.md", "CLAUDE.md"}

    def test_valid_relative_link(self):
        f = lint_links({"CLAUDE.md": "[待辦](docs/ops/BACKLOG.md)\n"}, self.PATHS)
        self.assertEqual(f, [])

    def test_dead_link(self):
        f = lint_links({"CLAUDE.md": "[死](docs/GONE.md)\n"}, self.PATHS)
        self.assertEqual(len(f), 1)
        self.assertIn("GONE", f[0]["msg"])

    def test_relative_from_subdir(self):
        f = lint_links({"docs/arc42/ARCHITECTURE.md": "[待辦](../ops/BACKLOG.md)\n"}, self.PATHS)
        self.assertEqual(f, [])

    def test_external_and_anchor_skipped(self):
        text = "[a](https://x.dev) [b](mailto:x@y.z) [c](#節)\n"
        self.assertEqual(lint_links({"CLAUDE.md": text}, self.PATHS), [])

    def test_link_with_anchor_checks_file_part(self):
        f = lint_links({"CLAUDE.md": "[x](docs/GONE.md#s)\n"}, self.PATHS)
        self.assertEqual(len(f), 1)


class TestLintLineRefs(unittest.TestCase):
    def test_line_ref_flagged(self):
        f = lint_line_refs({"docs/ops/NOTES.md": "詳 DESIGN.md:123 那段\n"})
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["level"], ERROR)

    def test_clean(self):
        self.assertEqual(lint_line_refs({"docs/ops/NOTES.md": "詳活書 §5、CLAUDE.md§3。\n"}), [])


class TestLintVolatileDeepLinks(unittest.TestCase):
    def test_deep_link_to_backlog_anchor(self):
        f = lint_volatile_deep_links({"CLAUDE.md": "[項](docs/ops/BACKLOG.md#b-021)\n"})
        self.assertEqual(len(f), 1)
        self.assertIn("整檔", f[0]["msg"])

    def test_deep_link_to_backlog_volume_anchor(self):
        # 滯後卷（BACKLOG-*.md）同屬揮發區——內部錨照禁
        f = lint_volatile_deep_links({"CLAUDE.md": "[項](docs/ops/BACKLOG-DEFERRED.md#b-060)\n"})
        self.assertEqual(len(f), 1)
        self.assertIn("整檔", f[0]["msg"])

    def test_whole_file_link_ok(self):
        f = lint_volatile_deep_links({"CLAUDE.md": "[待辦](docs/ops/BACKLOG.md)\n"})
        self.assertEqual(f, [])

    def test_state_and_notes_also_guarded(self):
        f = lint_volatile_deep_links(
            {"CLAUDE.md": "[a](docs/generated/STATE.md#x) [b](docs/ops/NOTES.md#y)\n"})
        self.assertEqual(len(f), 2)


class TestLintMemoryRefs(unittest.TestCase):
    def test_memory_path_flagged(self):
        f = lint_memory_refs({"docs/ops/NOTES.md": "見 ~/.claude/projects/x/memory/foo.md\n"})
        self.assertEqual(len(f), 1)

    def test_home_path_flagged(self):
        f = lint_memory_refs({"CLAUDE.md": "見 /home/anew/.claude/memory/bar.md\n"})
        self.assertEqual(len(f), 1)

    def test_rev3_annotation_exempt(self):
        self.assertEqual(
            lint_memory_refs({"docs/ops/LESSONS.md": "｜出處：rev3:memory/foo-bar\n"}), [])


class TestLintTense(unittest.TestCase):
    def test_clean_book(self):
        self.assertEqual(lint_tense("## §1 簡介\n系統現在長這樣。\n"), [])

    def test_forbidden_words(self):
        for word in ("待決", "TBD", "⏳", "已完成", "下一步"):
            f = lint_tense(f"## §6 Runtime\n這件事{word}中。\n")
            self.assertEqual(len(f), 1, msg=word)
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("去處", f[0]["msg"], msg=word)


class TestLintDictionary(unittest.TestCase):
    def test_rev3_codes_smuggled(self):
        f = lint_dictionary({"CLAUDE.md": "沿用 ⚠️c 與 待決③ 以及 F-12 的結論\n"})
        self.assertEqual(len(f), 3)
        self.assertTrue(all(x["level"] == WARN for x in f))

    def test_fast_changing_literals(self):
        f = lint_dictionary({BOOK: "服務聽 port 9528、seed 密碼 123456。\n"})
        self.assertEqual(len(f), 2)
        self.assertTrue(all("generated/reference" in x["msg"] for x in f))

    def test_provenance_line_exempt(self):
        f = lint_dictionary({BOOK: "｜出處：rev3:DECISIONS§1-⚠️c＋待決③\n"})
        self.assertEqual(f, [])

    def test_clean(self):
        self.assertEqual(lint_dictionary({"CLAUDE.md": "正常內容 §5 與 B-012。\n"}), [])

class TestLintEvents(unittest.TestCase):
    def test_valid_lines_pass(self):
        self.assertEqual(lint_events(_jl(VALID_CLOSE, VALID_MISC, VALID_REVIEW)), [])

    def test_empty_file_passes(self):
        self.assertEqual(lint_events(""), [])

    def test_bad_json(self):
        f = lint_events("{not json\n")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["level"], ERROR)
        self.assertIn("行 1", f[0]["where"])

    def test_missing_required_field(self):
        e = dict(VALID_CLOSE); e.pop("pins")
        f = lint_events(_jl(e))
        self.assertEqual(len(f), 1)
        self.assertIn("pins", f[0]["msg"])

    def test_unknown_type(self):
        f = lint_events(_jl({"type": "nope", "date": "2026-07-02"}))
        self.assertEqual(len(f), 1)
        self.assertIn("nope", f[0]["msg"])

    def test_arch_impact_none_ok(self):
        e = dict(VALID_CLOSE); e["arch_impact"] = "none"
        self.assertEqual(lint_events(_jl(e)), [])

    def test_arch_impact_bad(self):
        for bad in ("§6", ["x6"], []):
            e = dict(VALID_CLOSE); e["arch_impact"] = bad
            self.assertEqual(len(lint_events(_jl(e))), 1, msg=repr(bad))

    def test_bad_date(self):
        e = dict(VALID_MISC); e["date"] = "2026/07/02"
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_bad_kind(self):
        e = dict(VALID_CLOSE); e["kind"] = "diagonal"
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_review_findings_sum(self):
        e = json.loads(json.dumps(VALID_REVIEW)); e["findings"]["total"] = 5
        f = lint_events(_jl(e))
        self.assertEqual(len(f), 1)
        self.assertIn("total", f[0]["msg"])

    def test_blank_line_rejected(self):
        f = lint_events(json.dumps(VALID_MISC) + "\n\n" + json.dumps(VALID_MISC) + "\n")
        self.assertEqual(len(f), 1)

    def test_misc_backlog_done_valid(self):
        """misc 攜 backlog_done（輕量軌消化通道、2026-07-17 調規）——合法形零錯。"""
        e = dict(VALID_MISC); e["backlog_done"] = ["B-092", "B-098"]
        self.assertEqual(lint_events(_jl(e)), [])

    def test_misc_backlog_done_bad_ids(self):
        e = dict(VALID_MISC); e["backlog_done"] = ["X-1"]
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_backlog_done_ids_includes_misc(self):
        """_backlog_done_ids 掃 misc 通道——改壞掃描（如回退只掃 feature_close）即紅。"""
        m = dict(VALID_MISC); m["backlog_done"] = ["B-010"]
        self.assertEqual(_backlog_done_ids([VALID_CLOSE, m]), {"B-003", "B-010"})


class TestLintCloseExistence(unittest.TestCase):
    """L4：收刀事件引用之 ADR／backlog／specs 目錄存在性。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs/ops"))
        os.makedirs(os.path.join(self.root, ADR_DIR))

    def tearDown(self):
        self.tmp.cleanup()

    def _w(self, rel, content):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)

    def _adr(self, fid):
        self._w(f"{ADR_DIR}/{fid}-x.md", f'---\nid: "{fid}"\n---\n')

    def _close(self, **kw):
        e = {"type": "feature_close", "feature": "001-x", "merge": "abc1234",
             "date": "2026-07-10", "summary": "s", "pins": {"web": "a", "api": "b"},
             "adrs": [], "arch_impact": "none", "backlog_add": [], "backlog_done": []}
        e.update(kw)
        return e

    def _clean(self):
        # ADR 0007 存在、B-055 開放、B-003 已完成不在 BACKLOG、specs/001-x 存在
        self._adr("0007")
        self._w(BACKLOG, "<!-- next: B-100 -->\n# BACKLOG\n\n- B-055｜開放中\n")
        os.makedirs(os.path.join(self.root, "specs/001-x"))
        return self._close(adrs=["0007"], backlog_add=["B-055"], backlog_done=["B-003"])

    def test_clean_passes(self):
        self._w(EVENTS, _jl(self._clean()))
        self.assertEqual(lint_close_existence(self.root), [])

    def test_missing_adr(self):
        e = self._clean()
        e["adrs"] = ["0007", "0099"]  # 0099 無檔
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertEqual([x["code"] for x in f], ["L4"])
        self.assertIn("0099", f[0]["msg"])

    def test_backlog_done_still_open(self):
        e = self._clean()
        e["backlog_done"] = ["B-055"]  # B-055 仍開放在 BACKLOG＝未真的完成刪列
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("B-055" in x["msg"] and x["code"] == "L4" for x in f))

    def test_backlog_add_phantom(self):
        e = self._clean()
        e["backlog_add"] = ["B-077"]  # 既非開放亦無後續 done 消化
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("B-077" in x["msg"] and x["code"] == "L4" for x in f))

    def test_backlog_open_includes_deferred_volume(self):
        # 滯後卷條目仍屬開放：backlog_add 指向滯後卷不誤報 phantom；
        # backlog_done 誤標滯後中條目要被抓「宣稱完成卻未刪列」
        e = self._clean()
        self._w(BACKLOG, "<!-- next: B-100 -->\n# BACKLOG\n")
        self._w("docs/ops/BACKLOG-DEFERRED.md",
                "# BACKLOG-DEFERRED — 滯後卷\n\n- B-055｜開放中｜release 前\n")
        self._w(EVENTS, _jl(e))
        self.assertEqual(lint_close_existence(self.root), [])
        e["backlog_done"] = ["B-055"]
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("宣稱完成卻未刪列" in x["msg"] for x in f))

    def test_backlog_add_consumed_by_later_done(self):
        self._adr("0007")
        self._w(BACKLOG, "<!-- next: B-100 -->\n# BACKLOG\n")
        os.makedirs(os.path.join(self.root, "specs/001-x"))
        os.makedirs(os.path.join(self.root, "specs/002-y"))
        e1 = self._close(feature="001-x", adrs=["0007"], backlog_add=["B-056"])
        e2 = self._close(feature="002-y", adrs=["0007"], backlog_done=["B-056"])
        self._w(EVENTS, _jl(e1, e2))
        self.assertEqual(lint_close_existence(self.root), [])

    def test_missing_specs_dir(self):
        e = self._clean()
        e["feature"] = "009-nope"  # 未建 specs/009-nope
        self._w(EVENTS, _jl(e))
        f = lint_close_existence(self.root)
        self.assertTrue(any("specs/009-nope" in x["msg"] for x in f))

    def _git_close(self, backlog_at_merge, backlog_now, backlog_add):
        """建 git repo：commit＝merge M（BACKLOG＝backlog_at_merge）；工作樹 BACKLOG 改成 backlog_now
        （模擬事後完成刪列、git 即史）；events 寫 feature_close(merge=M, backlog_add)。回 findings。"""
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

        def g(*args):
            r = subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                               text=True, env=env)
            assert r.returncode == 0, r.stderr
            return r.stdout

        def _bl(ids):
            return "<!-- next: B-100 -->\n# BACKLOG\n\n" + "".join(f"- {b}｜開放中\n" for b in ids)
        self._adr("0007")
        os.makedirs(os.path.join(self.root, "specs/001-x"))
        self._w(BACKLOG, _bl(backlog_at_merge))
        g("init", "-q", "-b", "main")
        g("add", "-A")
        g("commit", "-qm", "merge-M")
        m = g("rev-parse", "HEAD").strip()
        self._w(BACKLOG, _bl(backlog_now))          # 事後刪列（工作樹）
        self._w(EVENTS, _jl(self._close(merge=m, adrs=["0007"], backlog_add=backlog_add)))
        return lint_close_existence(self.root)

    def test_backlog_add_removed_after_close_passes(self):
        # B-070 曾在 BACKLOG（commit M）、事後獨立完成刪列（現況/done 皆無）→git 史驗過、不誤報。
        # 回歸：舊碼查現況 open_ids/done_ids→獨立維護任務完成刪列後恆假陽（B-070 實測）。
        f = self._git_close(backlog_at_merge=["B-070"], backlog_now=[], backlog_add=["B-070"])
        self.assertEqual(f, [])

    def test_backlog_add_true_phantom_errors(self):
        # B-099 從未在 BACKLOG git 史出現（phantom/typo）→仍抓錯。
        f = self._git_close(backlog_at_merge=["B-070"], backlog_now=[], backlog_add=["B-099"])
        self.assertTrue(any("B-099" in x["msg"] and x["code"] == "L4" for x in f))


class TestLintReviewExistence(unittest.TestCase):
    """L5：review 分流引用（report 檔／to_backlog／wontfix_adr）存在性。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "docs/ops"))
        os.makedirs(os.path.join(self.root, ADR_DIR))

    def tearDown(self):
        self.tmp.cleanup()

    def _w(self, rel, content):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)

    def _adr(self, fid):
        self._w(f"{ADR_DIR}/{fid}-x.md", f'---\nid: "{fid}"\n---\n')

    def _review(self, **kw):
        e = {"type": "review", "date": "2026-08-01", "scope": "s",
             "report": "reviews/20260801-x.md",
             "findings": {"total": 1, "fixed": 0, "to_backlog": [], "wontfix_adr": []}}
        e.update(kw)
        return e

    def _clean(self):
        self._adr("0012")
        self._w(BACKLOG, "<!-- next: B-100 -->\n# BACKLOG\n\n- B-055｜開放中\n")
        self._w("docs/reviews/20260801-x.md", "# review\n")
        return self._review(findings={"total": 2, "fixed": 0,
                                       "to_backlog": ["B-055"], "wontfix_adr": ["0012"]})

    def test_clean_passes(self):
        self._w(EVENTS, _jl(self._clean()))
        self.assertEqual(lint_review_existence(self.root), [])

    def test_empty_events_vacuous_pass(self):
        self._w(EVENTS, "")
        self.assertEqual(lint_review_existence(self.root), [])

    def test_missing_report(self):
        e = self._clean()
        e["report"] = "reviews/nope.md"  # 檔不存在
        self._w(EVENTS, _jl(e))
        f = lint_review_existence(self.root)
        self.assertTrue(any("report" in x["msg"] and x["code"] == "L5" for x in f))

    def test_missing_wontfix_adr(self):
        e = self._clean()
        e["findings"]["wontfix_adr"] = ["0099"]  # 無檔
        self._w(EVENTS, _jl(e))
        f = lint_review_existence(self.root)
        self.assertTrue(any("0099" in x["msg"] and x["code"] == "L5" for x in f))

    def test_to_backlog_phantom(self):
        e = self._clean()
        e["findings"]["to_backlog"] = ["B-077"]  # 既非開放亦無 done 消化
        self._w(EVENTS, _jl(e))
        f = lint_review_existence(self.root)
        self.assertTrue(any("B-077" in x["msg"] and x["code"] == "L5" for x in f))


BOOK_3SEC = "# 活書\n\n## §1 甲\n一\n## §2 乙\n二\n## §3 丙\n三\n"


class TestLintArchImpact(unittest.TestCase):
    """L6：arch_impact 節存在性（a）＋最新刀 merge→HEAD 雙向（b）。"""

    def test_changed_sections_content_diff(self):
        a = "## §5 X\naaa\n## §6 Y\nbbb\n"
        b = "## §5 X\nAAA\n## §6 Y\nbbb\n"  # 僅 §5 內容變
        self.assertEqual(_arch_changed_sections(a, b), {5})

    def test_changed_sections_added(self):
        a = "## §5 X\naaa\n"
        b = "## §5 X\naaa\n## §6 Y\nbbb\n"  # §6 新增
        self.assertEqual(_arch_changed_sections(a, b), {6})

    def _write_book_events(self, d, arch_impact):
        os.makedirs(os.path.join(d, "docs/ops"))
        os.makedirs(os.path.join(d, "docs/arc42"))
        with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
            fh.write(BOOK_3SEC)
        ev = {"type": "feature_close", "feature": "001-x", "merge": "abc1234",
              "date": "2026-07-10", "summary": "s", "pins": {"web": "a", "api": "b"},
              "adrs": [], "arch_impact": arch_impact, "backlog_add": [], "backlog_done": []}
        with open(os.path.join(d, EVENTS), "w", encoding="utf-8") as fh:
            fh.write(_jl(ev))

    def test_existence_clean_no_git_skips_b(self):
        # 非 git 目錄＋不可解 merge SHA→(b) 跳過；(a) 驗 §2 存在→0
        with tempfile.TemporaryDirectory() as d:
            self._write_book_events(d, ["§2"])
            self.assertEqual(lint_arch_impact(d), [])

    def test_existence_bad_section(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_book_events(d, ["§99"])
            f = lint_arch_impact(d)
            self.assertTrue(any("§99" in x["msg"] and x["code"] == "L6" for x in f))

    def _git_repo(self, d, arch_impact, commit_bookkeeping=True):
        """建 git repo：commit1＝merge M（活書 v1）；簿記 as-built（活書僅改 §5 內容）＋events 寫工作樹。
        commit_bookkeeping=True→再 commit 成簿記 commit（post-commit 態、HEAD＝簿記）；
        False→as-built／events 留工作樹不 commit（pre-commit 閘態、HEAD 仍＝merge M）。回 lint_arch_impact。"""
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

        def g(*args):
            r = subprocess.run(["git", *args], cwd=d, capture_output=True,
                               text=True, env=env)
            assert r.returncode == 0, r.stderr
            return r.stdout
        g("init", "-q", "-b", "main")
        os.makedirs(os.path.join(d, "docs/arc42"))
        os.makedirs(os.path.join(d, "docs/ops"))
        with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
            fh.write("## §5 A\nold5\n## §6 B\nold6\n")
        g("add", "-A")
        g("commit", "-qm", "merge-M")
        m = g("rev-parse", "HEAD").strip()
        with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
            fh.write("## §5 A\nNEW5\n## §6 B\nold6\n")  # 簿記僅改 §5 內容
        ev = {"type": "feature_close", "feature": "001-x", "merge": m,
              "date": "2026-07-10", "summary": "s", "pins": {"web": "a", "api": "b"},
              "adrs": [], "arch_impact": arch_impact, "backlog_add": [], "backlog_done": []}
        with open(os.path.join(d, EVENTS), "w", encoding="utf-8") as fh:
            fh.write(_jl(ev))
        if commit_bookkeeping:
            g("add", "-A")
            g("commit", "-qm", "bookkeeping")
        return lint_arch_impact(d)

    def test_bidirectional_clean(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])

    def test_bidirectional_precommit_clean(self):
        # pre-commit 閘時刻（HEAD＝merge、as-built 僅在工作樹）：宣稱 §5＝實改 §5→應綠。
        # 回歸：舊碼讀 head_file(HEAD) 時 merge→HEAD 恆為空、此處會誤報「宣稱但無變動」。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"], commit_bookkeeping=False), [])

    def test_bidirectional_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            f = self._git_repo(d, ["§6"])  # 宣稱 §6，實際改的是 §5
            l6 = [x for x in f if x["code"] == "L6"]
            msgs = " ".join(x["msg"] for x in l6)
            self.assertEqual(len(l6), 2)
            self.assertIn("§6", msgs)  # 宣稱卻沒改
            self.assertIn("§5", msgs)  # 改了卻沒宣稱

    def _runner(self, d):
        """回一個對 tempdir d 執行 git 的 runner（與 _git_repo 同環境）。"""
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

        def g(*args):
            r = subprocess.run(["git", *args], cwd=d, capture_output=True,
                               text=True, env=env)
            assert r.returncode == 0, r.stderr
            return r.stdout
        return g

    def test_bidirectional_next_feature_committed_skips_b(self):
        # 下一支 feature 於某單元 commit 編輯活書 §6（mid-feature、最新 close 仍＝001-x）：
        # HEAD 前進超過簿記（HEAD^＝簿記 B≠merge M）→ (b) 應跳過、不誤報。
        # 回歸 blocker：舊碼恆讀工作樹→ merge→工作樹＝{5,6}、claimed={5}→ 假陽全程硬擋下一支 feature。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])  # 建到簿記 post-commit（HEAD=B）
            g = self._runner(d)
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write("## §5 A\nNEW5\n## §6 B\nDRIFT6\n")  # 007 動 §6
            g("add", "-A")
            g("commit", "-qm", "007-unit-book")
            self.assertEqual(lint_arch_impact(d), [])

    def test_bidirectional_next_feature_uncommitted_reads_head(self):
        # 下一支 feature 活書漂移仍在工作樹未 commit（HEAD 仍＝簿記 B、HEAD^＝merge M）：
        # (b) 綁 State 2 讀 HEAD 版活書（非工作樹）→ 忽略漂移、不誤報。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write("## §5 A\nNEW5\n## §6 B\nDRIFT6\n")  # 工作樹漂移未 commit
            self.assertEqual(lint_arch_impact(d), [])

    def test_bidirectional_next_feature_unrelated_commit_skips_b(self):
        # 下一支 feature 已 commit 一筆活書 §6 後、再來一筆無關（僅 NOTES）commit：
        # HEAD 仍在簿記之後 → (b) 續跳過、無關 commit 不被誤擋（回歸 blocker「連改 NOTES 亦被擋」）。
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._git_repo(d, ["§5"]), [])
            g = self._runner(d)
            with open(os.path.join(d, BOOK), "w", encoding="utf-8") as fh:
                fh.write("## §5 A\nNEW5\n## §6 B\nDRIFT6\n")
            g("add", "-A")
            g("commit", "-qm", "007-unit-book")
            with open(os.path.join(d, "docs/ops/NOTES.md"), "w", encoding="utf-8") as fh:
                fh.write("下一步\n")
            g("add", "-A")
            g("commit", "-qm", "007-notes")
            self.assertEqual(lint_arch_impact(d), [])


class TestLintBudgets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        for d in ("docs/ops", "docs/generated", "docs/arc42"):
            os.makedirs(os.path.join(self.root, d))

    def tearDown(self):
        self.tmp.cleanup()

    def _w(self, rel, content):
        p = os.path.join(self.root, rel)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)

    def test_all_missing_files_pass(self):
        self.assertEqual(lint_budgets(self.root), [])

    def test_notes_over_40_lines(self):
        self._w("docs/ops/NOTES.md", "x\n" * 41)
        f = lint_budgets(self.root)
        self.assertEqual([x["code"] for x in f], ["L7"])
        self.assertEqual(f[0]["level"], ERROR)

    def test_notes_at_40_lines_ok(self):
        self._w("docs/ops/NOTES.md", "x\n" * 40)
        self.assertEqual(lint_budgets(self.root), [])

    def test_state_over_4k_tokens(self):
        self._w("docs/generated/STATE.md", "字" * 4001 * 1)  # 4001 chars ×3 bytes → >4000 tokens
        f = lint_budgets(self.root)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["level"], ERROR)

    def test_lessons_warn_near_limit(self):
        self._w("docs/ops/LESSONS.md", "字" * 22600)  # ~22600 tokens：警告未達硬擋
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [WARN])

    def test_lessons_volume_files_also_checked(self):
        self._w("docs/ops/LESSONS-001-050.md", "字" * 25100)
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [ERROR])

    def test_backlog_volume_files_also_checked(self):
        # BACKLOG-*.md 卷走 glob 限額（同主檔 200 行）——新卷免登記 BUDGETS 也被攔
        self._w("docs/ops/BACKLOG-ARCHIVE.md", "x\n" * 201)
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [ERROR])

    def test_architecture_section_quota_warn(self):
        body = "## §1 簡介與目標\n" + "內容\n" * 41 + "## §2 約束\n內容\n"
        self._w("docs/arc42/ARCHITECTURE.md", body)
        f = lint_budgets(self.root)
        self.assertEqual([x["level"] for x in f], [WARN])
        self.assertIn("§1", f[0]["msg"])

    def test_architecture_over_700_lines_error(self):
        self._w("docs/arc42/ARCHITECTURE.md", "## §1 簡介與目標\n" + "x\n" * 700)
        levels = [x["level"] for x in lint_budgets(self.root)]
        self.assertIn(ERROR, levels)


class TestTokenCount(unittest.TestCase):
    """鎖定 token 算法：UTF-8 bytes ÷ 3。"""

    def test_ascii(self):
        self.assertEqual(token_count("abc"), 1)      # 3 bytes → 1

    def test_empty(self):
        self.assertEqual(token_count(""), 0)

    def test_cjk(self):
        self.assertEqual(token_count("中文字"), 3)    # 9 bytes → 3

    def test_mixed_floor(self):
        self.assertEqual(token_count("ab"), 0)       # 2 bytes → 0（整數除法）
        self.assertEqual(token_count("abcd"), 1)     # 4 bytes → 1


class TestFrontMatter(unittest.TestCase):
    ADR = (
        "---\n"
        'id: "0007"\n'
        "title: 測試決策\n"
        "date: 2026-07-02\n"
        "status: accepted\n"
        "feature: 001-demo\n"
        "supersedes: [0003, 0004]\n"
        "superseded_by: []\n"
        "tags: [auth]\n"
        "---\n"
        "\n## 背景\n內文\n"
    )

    def test_basic_fields(self):
        meta, body = parse_front_matter(self.ADR)
        self.assertEqual(meta["id"], "0007")
        self.assertEqual(meta["title"], "測試決策")
        self.assertEqual(meta["status"], "accepted")

    def test_flow_lists(self):
        meta, _ = parse_front_matter(self.ADR)
        self.assertEqual(meta["supersedes"], ["0003", "0004"])
        self.assertEqual(meta["superseded_by"], [])

    def test_body_preserved(self):
        _, body = parse_front_matter(self.ADR)
        self.assertEqual(body, "\n## 背景\n內文\n")

    def test_no_front_matter(self):
        meta, body = parse_front_matter("# 純文件\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# 純文件\n")


class TestReviewFixes(unittest.TestCase):
    """B4 對抗式 review 的 CONFIRMED findings 回歸測試。"""

    # --- 崩潰型 ---
    def test_event_non_object_line_is_finding_not_crash(self):
        for bad in ("123", '"text"', "[1,2]", "null"):
            f = lint_events(bad + "\n")
            self.assertEqual(len(f), 1, msg=bad)
            self.assertIn("object", f[0]["msg"])
        self.assertEqual(parse_events_loose('[1,2]\n{"type":"misc"}\n'), [{"type": "misc"}])

    def test_adr_id_as_list_no_crash(self):
        bad = ADR_OK_B.replace('id: "0002"', "id: [0002]")
        f = lint_adrs({"0002-new.md": bad, "0001-old.md": ADR_OK_A}, {})
        self.assertTrue(any("id" in x["msg"] for x in f))  # 有 finding、無 TypeError

    def test_backfill_skips_adr_without_id(self):
        no_id = "---\ntitle: 無 id\ndate: 2026-07-09\nstatus: draft\nsupersedes: [0001]\n---\nbody\n"
        changed = backfill_supersessions({"0001-old.md": ADR_OK_A, "0003-x.md": no_id})
        self.assertNotIn("0003-x.md", changed)  # 不崩潰；缺 id 由 L8 報

    def test_l3_int_adrs_rejected(self):
        e = dict(VALID_CLOSE); e["adrs"] = [1234]
        self.assertEqual(len(lint_events(_jl(e))), 1)

    def test_adr_duplicate_id_detected(self):
        a = ADR_OK_A.replace("supersedes: []", "supersedes: []").replace(
            'id: "0001"', 'id: "0002"').replace("status: superseded", "status: draft") \
            .replace("superseded_by: [0002]", "superseded_by: []")
        f = lint_adrs({"0002-foo.md": a.replace("0002-", ""),
                       "0002-new.md": ADR_OK_B.replace("supersedes: [0001]", "supersedes: []")}, {})
        self.assertTrue(any("重複" in x["msg"] for x in f))

    # --- L3 review findings 元素驗證 ---
    def test_review_findings_elements_validated(self):
        e = json.loads(json.dumps(VALID_REVIEW))
        e["findings"] = {"total": 2, "fixed": 0, "to_backlog": ["banana", "B-009"],
                         "wontfix_adr": []}
        self.assertEqual(len(lint_events(_jl(e))), 1)
        e["findings"] = {"total": -1, "fixed": -1, "to_backlog": [], "wontfix_adr": []}
        self.assertEqual(len(lint_events(_jl(e))), 1)

    # --- L11 ---
    def test_l11_exemption_only_line_initial(self):
        f = lint_dictionary({BOOK: "沿用 ⚠️c 的結論做 X｜出處：rev3:DECISIONS§1\n"})
        self.assertEqual(len(f), 1)  # 行中出處標註不豁免
        self.assertEqual(lint_dictionary({BOOK: "｜出處：rev3:DECISIONS§1-⚠️c\n"}), [])

    def test_l11_route_count_pattern(self):
        f = lint_dictionary({BOOK: "全站共 54 條路由。\n"})
        self.assertEqual(len(f), 1)
        self.assertIn("route", f[0]["msg"].lower() + "route")  # 有命中即可

    def test_l11_seed_password_boundary(self):
        self.assertEqual(lint_dictionary({BOOK: "對照 commit a1234567 的變更。\n"}), [])
        self.assertEqual(len(lint_dictionary({BOOK: "密碼123456。\n"})), 1)

    # --- L8 ---
    def test_l8_optional_field_types_validated(self):
        bad = ADR_OK_B.replace("supersedes: [0001]", "supersedes: []") \
                      .replace("superseded_by: []", "superseded_by: []\ntags: notalist")
        f = lint_adrs({"0002-new.md": bad}, {})
        self.assertTrue(any("tags" in x["msg"] for x in f))

    def test_amend_only_exempts_body(self):
        cur = ADR_OK_B.replace("title: 乙決策", "title: 被改名") \
                      .replace("新案。", "順便改 body。")
        f = lint_adrs({"0001-old.md": ADR_OK_A, "0002-new.md": cur},
                      {"0001-old.md": ADR_OK_A, "0002-new.md": ADR_OK_B}, amend=True)
        self.assertEqual(len(f), 1)  # body 豁免、title 不豁免
        self.assertIn("title", f[0]["msg"])

    # --- 事件行界與編碼 ---
    def test_u2028_inside_event_string_ok(self):
        e = dict(VALID_MISC); e["summary"] = "前 後"
        self.assertEqual(lint_events(_jl(e)), [])
        self.assertEqual(len(parse_events_loose(_jl(e))), 1)

    def test_read_strips_bom(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.md"), "w", encoding="utf-8-sig") as fh:
                fh.write("---\nid: \"0001\"\n---\nbody\n")
            text = _read(d, "x.md")
        self.assertTrue(text.startswith("---"))

    # --- MILESTONES 壞 date ---
    def test_milestones_bad_date_stays_in_main_volume(self):
        bad = dict(VALID_MISC); bad["date"] = "not-a-date"
        files = gen_milestones([VALID_MISC, bad])
        self.assertEqual(set(files), {"docs/generated/MILESTONES.md"})
        self.assertIn("bootstrap 完成", files["docs/generated/MILESTONES.md"])
        self.assertIn("not-a-date", files["docs/generated/MILESTONES.md"])


class TestGitIntegration(unittest.TestCase):
    """git 介接：fail-closed 閘、HEAD 批次載入、staged 落差偵測（用臨時 git repo）。"""

    def _init_repo(self, d):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        def g(*args):
            r = subprocess.run(["git", *args], cwd=d, capture_output=True, text=True, env=env)
            assert r.returncode == 0, r.stderr
        g("init", "-q", "-b", "main")
        os.makedirs(os.path.join(d, ADR_DIR))
        os.makedirs(os.path.join(d, "docs/generated"))
        with open(os.path.join(d, ADR_DIR, "0001-x.md"), "w", encoding="utf-8") as fh:
            fh.write(ADR_OK_A)
        with open(os.path.join(d, "docs/generated/STATE.md"), "w", encoding="utf-8") as fh:
            fh.write("v1\n")
        g("add", "-A")
        g("commit", "-qm", "init")
        return g

    def test_lint_fails_closed_without_git(self):
        with tempfile.TemporaryDirectory() as d:
            f = run_lint(d)
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["level"], ERROR)
            self.assertIn("git", f[0]["msg"])

    def test_load_head_adrs_batch(self):
        with tempfile.TemporaryDirectory() as d:
            self._init_repo(d)
            head = load_head_adrs(d)
            self.assertEqual(list(head), ["0001-x.md"])
            self.assertEqual(head["0001-x.md"], ADR_OK_A)

    def test_cli_errata_smoke(self):
        """回歸：cmd_errata 曾漏傳 root 而 TypeError 崩潰（CLI 包裝層無測試覆蓋）。"""
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "errata", "next-id"],
                           capture_output=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("errata", r.stdout)

    def test_unstaged_generated_detected(self):
        with tempfile.TemporaryDirectory() as d:
            self._init_repo(d)
            self.assertEqual(unstaged_generated(d), [])
            with open(os.path.join(d, "docs/generated/STATE.md"), "w", encoding="utf-8") as fh:
                fh.write("v2（generate 過但沒 git add）\n")
            self.assertEqual(unstaged_generated(d), ["docs/generated/STATE.md"])


class TestCredScan(unittest.TestCase):
    """L16 憑證內容掃描（contracts G1／data-model §1§2）：樣式集、外層全量、增量、退化、self-test。

    ★本類全部紅樣本一律以執行期字串串接構造——本檔屬 tracked，落任何完整命中字面即會被 L16
    掃自己時自命中自紅（analyze 對 U1 的預警）；`test_tool_source_has_no_credential_literal`
    即該紀律的反證案。
    """

    # 與 `_cred_samples()`（產線 self-test 樣本）刻意各自獨立：樣本產生器壞掉時測試仍抓得到
    RED = {
        "pem-private-key": "-----BEGIN " + "OPENSSH PRIVATE" + " KEY" + "-----",
        "aws-akia": "AKIA" + "Z7Q3M8K2P5R9T4W6",
        "github-token": "gh" + "o_" + "Zq7" * 12,
        "github-pat": "github" + "_pat_" + "K3m" * 8,
    }
    GREEN = (
        "普通說明文字，無任何憑證內容。",
        "-----BEGIN CERTIFICATE-----",                       # 憑證公開部分、非私鑰
        "AKIA" + "SHORT12345",                               # AKIA 形但長度不足 16
        "gh" + "p_" + "ab12",                                # token 形但長度不足 36
        "github" + "_pat_" + "tooShort",                     # PAT 形但長度不足 22
        # ★下界邊界樣本（恰比下界少一位）：無此兩筆時「把下界放寬」型突變（36→20、22→10）
        # 全套仍全綠——長度不足很多的樣本擋不住小幅放寬（U2 審查突變實證）。
        "gh" + "p_" + "Zq7" * 11 + "AB",                     # token 形、35 位＝下界 36 少一
        "github" + "_pat_" + "K3m" * 7,                      # PAT 形、21 位＝下界 22 少一
        "密碼欄 password=hunter2 屬刻意排除面（誤報成本高於殘餘風險）",
    )

    # -- fixture 工具 ------------------------------------------------------
    def _g(self, cwd, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, msg=f"git {args}｜{r.stderr}")
        return r.stdout

    def _outer(self, d):
        """外層 fixture repo（L16 只需 tracked 清單與 staged 面、毋需 docs 骨架）。"""
        self._g(d, "init", "-q", "-b", "main")
        self._write(d, "README.md", "普通說明\n")
        self._g(d, "add", "README.md")
        self._g(d, "commit", "-qm", "init")

    def _write(self, d, rel, text):
        path = os.path.join(d, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def _subrepo(self, d, name, label="aws-akia"):
        """子 repo：commit A 乾淨、commit B 新增行含指定 label 紅樣本；回 (shaA, shaB)。"""
        sd = os.path.join(d, name)
        os.makedirs(sd)
        self._g(sd, "init", "-q", "-b", "main")
        self._write(sd, "app.ts", "export const a = 1\n")
        self._g(sd, "add", "app.ts")
        self._g(sd, "commit", "-qm", "A")
        sha_a = self._g(sd, "rev-parse", "HEAD").strip()
        self._write(sd, "app.ts",
                    "export const a = 1\nconst k = '" + self.RED[label] + "'\n")
        self._g(sd, "add", "app.ts")
        self._g(sd, "commit", "-qm", "B")
        return sha_a, self._g(sd, "rev-parse", "HEAD").strip()

    def _stage_gitlink(self, d, name, sha):
        self._g(d, "update-index", "--add", "--cacheinfo", f"160000,{sha},{name}")

    def _real_diff(self, d, first, second):
        """以真 git 產出 `app.ts` 的 -U0 diff（手寫 diff 會與 git 實際輸出漂移）。"""
        self._g(d, "init", "-q", "-b", "main")
        self._write(d, "app.ts", first)
        self._g(d, "add", "app.ts")
        self._g(d, "commit", "-qm", "A")
        self._write(d, "app.ts", second)
        self._g(d, "add", "app.ts")
        self._g(d, "commit", "-qm", "B")
        return self._g(d, "diff", "HEAD~1", "HEAD", "-U0")

    # -- 樣式集（data-model §1） -------------------------------------------
    def test_red_samples_hit_each_label(self):
        for label, sample in self.RED.items():
            with self.subTest(label=label):
                self.assertEqual([l for l, _ in scan_cred_text(sample)], [label])

    def test_green_samples_no_hit(self):
        for sample in self.GREEN:
            with self.subTest(sample=sample[:24]):
                self.assertEqual(scan_cred_text(sample), [])

    def test_scan_reports_line_number(self):
        text = "第一行\n第二行\n" + self.RED["pem-private-key"] + "\n"
        self.assertEqual(scan_cred_text(text), [("pem-private-key", 3)])

    def test_tool_source_has_no_credential_literal(self):
        """★A8 反證：本工具原始碼（tracked）零完整命中字面——否則 G1 掃自己即自紅。"""
        with open(os.path.abspath(__file__), encoding="utf-8", errors="replace") as fh:
            self.assertEqual(scan_cred_text(fh.read()), [])

    # -- 外層全量面（data-model §2 第 1 列） --------------------------------
    def test_outer_scan_reports_tracked_hit(self):
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "deploy/key.conf", "cert:\n" + self.RED["pem-private-key"] + "\n")
            self._g(d, "add", "deploy/key.conf")
            f = lint_cred_outer(d)
            self.assertEqual([x["level"] for x in f], [ERROR])
            self.assertIn("deploy/key.conf", f[0]["where"])
            self.assertIn("pem-private-key", f[0]["msg"])

    def test_outer_scan_catches_staged_when_worktree_file_removed(self):
        """★staged 含憑證但工作樹檔已 rm：只看工作樹＝零信號放行（index blob 仍要進版控）。

        連帶驗「沒掃到必留信號」：工作樹讀不到一律落 WARN、不得靜默當乾淨。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "key.conf", "k='" + self.RED["aws-akia"] + "'\n")
            self._g(d, "add", "key.conf")
            os.remove(os.path.join(d, "key.conf"))
            f = lint_cred_outer(d)
            errs = [x for x in f if x["level"] == ERROR]
            self.assertEqual(len(errs), 1, msg=str(f))
            self.assertIn("key.conf", errs[0]["where"])
            self.assertIn("aws-akia", errs[0]["msg"])
            self.assertTrue(any(x["level"] == WARN and "key.conf" == x["where"] for x in f),
                            msg=str(f))

    def test_outer_scan_catches_staged_when_worktree_cleaned(self):
        """staged 髒、工作樹版本已洗白：判定面取自 index 才對得上「這次 commit 的內容」。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "key.conf", "k='" + self.RED["github-token"] + "'\n")
            self._g(d, "add", "key.conf")
            self._write(d, "key.conf", "k='已移除'\n")
            f = lint_cred_outer(d)
            self.assertEqual([x["level"] for x in f], [ERROR], msg=str(f))
            self.assertIn("key.conf", f[0]["where"])
            self.assertIn("github-token", f[0]["msg"])

    def test_outer_scan_clean_repo_is_green(self):
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self.assertEqual(lint_cred_outer(d), [])

    def test_outer_scan_skips_binary(self):
        """前 8KB 含 NUL＝二進位、不掃（R2）。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            blob = b"\x00\x01" + self.RED["pem-private-key"].encode() + b"\x00"
            with open(os.path.join(d, "logo.bin"), "wb") as fh:
                fh.write(blob)
            self._g(d, "add", "logo.bin")
            self.assertEqual(lint_cred_outer(d), [])

    def test_outer_scan_excludes_gitlink_entry(self):
        """gitlink 條目屬目錄、不入外層掃描面（其內容歸增量面）。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            _, sha_b = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_b)
            self.assertEqual(lint_cred_outer(d), [])

    # -- submodule 增量面（data-model §2 第 2/3 列、R3） ---------------------
    def test_submodule_incremental_hit(self):
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, sha_b = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_a)
            self._g(d, "commit", "-qm", "pin A")
            self._stage_gitlink(d, "base-web", sha_b)
            f = lint_cred_submodules(d)
            errs = [x for x in f if x["level"] == ERROR]
            self.assertEqual(len(errs), 1, msg=str(f))
            self.assertIn("base-web", errs[0]["where"])
            self.assertIn("app.ts", errs[0]["where"])
            self.assertIn("aws-akia", errs[0]["msg"])

    def test_diff_hits_scans_content_line_starting_with_double_plus(self):
        """★檔案內以「兩個加號加空白」起首的行，在 -U0 diff 長成三個加號——不得當檔頭吞掉。"""
        with tempfile.TemporaryDirectory() as d:
            diff = self._real_diff(
                d, "x = 1\n",
                "x = 1\n++ 文件裡的 diff 片段 " + self.RED["aws-akia"] + "\n")
            self.assertIn("\n+++ 文件裡", diff)      # 前提：git 確實把它輸出成三個加號起首
            self.assertEqual(cred_diff_hits(diff), [("app.ts", "aws-akia")])

    def test_diff_hits_double_plus_line_does_not_pollute_path(self):
        """誤判成檔頭時 path 會被寫成該行內容，其後真命中即指名一個不存在的檔。"""
        with tempfile.TemporaryDirectory() as d:
            diff = self._real_diff(
                d, "x = 1\n",
                "x = 1\n++ 文件裡的 diff 片段\nconst k = '" + self.RED["github-token"] + "'\n")
            self.assertEqual(cred_diff_hits(diff), [("app.ts", "github-token")])

    def test_submodule_not_staged_means_no_scan(self):
        """未 stage gitlink＝不觸發增量面（成本正比變更量）。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, _ = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_a)
            self._g(d, "commit", "-qm", "pin A")
            self.assertEqual(lint_cred_submodules(d), [])

    def test_submodule_fallback_full_tree_when_old_pin_unresolvable(self):
        """舊 pin 不可解→退化為新 pin 全樹掃＋WARN 註記（fail-closed 向完整掃）。

        ★逐 label 參數化不可省：退化面是唯一走 git 自己 ERE 引擎的路徑（其餘面走
        python re），兩套引擎對同一份樣式集未必等價；只測單一 label 會漏掉引擎歧異——
        實證即以連字號開頭的 PEM 樣式在缺 `-e` 時被 git 當未知選項吞成零命中。
        """
        for label in self.RED:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as d:
                self._outer(d)
                _, sha_b = self._subrepo(d, "base-web", label)
                self._stage_gitlink(d, "base-web", "0" * 39 + "1")   # 子庫不存在之物件
                self._g(d, "commit", "-qm", "pin 不可解")
                self._stage_gitlink(d, "base-web", sha_b)
                f = lint_cred_submodules(d)
                self.assertTrue(any(x["level"] == WARN and "退化" in x["msg"] for x in f),
                                msg=str(f))
                errs = [x for x in f if x["level"] == ERROR]
                self.assertEqual(len(errs), 1, msg=str(f))
                self.assertIn(label, errs[0]["msg"])
                self.assertIn("app.ts", errs[0]["where"])

    def test_submodule_fallback_scan_failure_is_fail_closed(self):
        """★退化掃本身跑不成（新 pin 物件不在該庫，如切分支後未 fetch）→ERROR 不放行。

        「非零退出即零命中」會把執行失敗讀成乾淨，同時 WARN 還宣稱已退化為全樹掃——
        形成比不掃更危險的假保證（FR-008 fail-closed）。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", "0" * 39 + "1")   # 舊 pin 不可解→走退化
            self._g(d, "commit", "-qm", "pin 不可解")
            self._stage_gitlink(d, "base-web", "0" * 39 + "2")   # 新 pin 物件亦不在該庫
            f = lint_cred_submodules(d)
            errs = [x for x in f if x["level"] == ERROR]
            self.assertEqual(len(errs), 1, msg=str(f))
            self.assertIn("退化全樹掃執行失敗", errs[0]["msg"])

    def test_fallback_full_tree_skips_binary(self):
        """★退化全樹掃須與外層面同規則跳過二進位（R2）。

        缺 `-I` 時 git grep 對二進位檔改輸出「Binary file <tree>:<path> matches」——逐冒號
        切欄後路徑欄變成「<path> matches」殘餘文字，命中被指名到一個不存在的檔；且二進位
        面的判定與外層面（前 8KB 含 NUL 即 skip）不一致。
        """
        with tempfile.TemporaryDirectory() as d:
            sd = os.path.join(d, "base-web")
            os.makedirs(sd)
            self._g(sd, "init", "-q", "-b", "main")
            with open(os.path.join(sd, "logo.bin"), "wb") as fh:
                fh.write(b"\x00\x01" + self.RED["aws-akia"].encode() + b"\x00")
            self._g(sd, "add", "logo.bin")
            self._g(sd, "commit", "-qm", "bin")
            sha = self._g(sd, "rev-parse", "HEAD").strip()
            self.assertEqual(_cred_grep_tree(sd, sha), ([], None))

    def test_grep_tree_reports_no_hit_without_error(self):
        """乾淨 tree：git grep 退出碼 1＝確無命中，MUST NOT 誤判成掃描失敗。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, _ = self._subrepo(d, "base-web")
            self.assertEqual(_cred_grep_tree(os.path.join(d, "base-web"), sha_a), ([], None))

    def test_submodule_absent_worktree_skips(self):
        """worktree 缺席（唯讀看碼模式）→跳過、不落 ERROR。"""
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._stage_gitlink(d, "rust-api", "1" * 40)
            f = lint_cred_submodules(d)
            self.assertEqual([x["level"] for x in f], [WARN])
            self.assertIn("跳過", f[0]["msg"])

    # -- 組裝與 run_lint 接線（contracts G1「觸發＝每次 lint」） ---------------
    def test_credentials_assembly_wires_submodule_face(self):
        """★組裝層：`lint_cred_submodules` 從 `lint_credentials` 掉線＝US2 情境 2 靜默下線。

        突變實證：組裝行改成只回 self-test＋外層面後，全套測試仍全綠——各面單元測試都直呼
        函式本體、繞過組裝層，故「函式活著、接線斷掉」零信號。本案即補那張網。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            sha_a, sha_b = self._subrepo(d, "base-web")
            self._stage_gitlink(d, "base-web", sha_a)
            self._g(d, "commit", "-qm", "pin A")
            self._stage_gitlink(d, "base-web", sha_b)
            f = lint_credentials(d)
            self.assertTrue(
                any(x["code"] == "L16" and x["level"] == ERROR
                    and "base-web" in x["where"] and "app.ts" in x["where"] for x in f),
                msg=str(f))

    def test_credentials_assembly_wires_self_test(self):
        """★組裝層：`cred_self_test` 掉線＝US2 情境 5 防恆綠靜默下線（同上突變實證）。

        乾淨 fixture＋永不命中之 dead 樣式集：外層面與增量面必然零 ERROR，故任何 ERROR
        只可能來自 self-test——信號純淨。
        """
        dead = (("pem-private-key", re.compile(r"ZZZ-NEVER-MATCH-ZZZ")),)
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            f = self._with_patterns(dead, lambda: lint_credentials(d))
            self.assertTrue(
                any(x["code"] == "L16" and x["level"] == ERROR
                    and "self-test 失效" in x["msg"] for x in f), msg=str(f))

    def test_run_lint_wires_credential_gate(self):
        """★接線層：`lint_credentials` 從 run_lint 掉線＝G1 整條下線，單元測試卻不會有反應。

        突變實證：刪掉 run_lint 內該接線行後全套測試仍全綠——本案即補那張網
        （U5 T020 要重組 run_lint，重組時掉線必須當場紅）。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "deploy/key.conf", "cert:\n" + self.RED["pem-private-key"] + "\n")
            self._g(d, "add", "deploy/key.conf")
            f = run_lint(d)
            self.assertTrue(
                any(x["code"] == "L16" and x["level"] == ERROR
                    and "deploy/key.conf" in x["where"] for x in f), msg=str(f))

    # -- self-test 防恆綠（contracts G1） -----------------------------------
    def test_self_test_green_on_healthy_engine(self):
        self.assertEqual(cred_self_test(), [])

    def _with_patterns(self, patterns, fn):
        original = globals()["CRED_PATTERNS"]
        globals()["CRED_PATTERNS"] = patterns
        try:
            return fn()
        finally:
            globals()["CRED_PATTERNS"] = original

    def _with_whitelist(self, whitelist, fn):
        original = globals()["CRED_WHITELIST"]
        globals()["CRED_WHITELIST"] = whitelist
        try:
            return fn()
        finally:
            globals()["CRED_WHITELIST"] = original

    def test_whitelist_suppresses_both_outer_faces(self):
        """★`CRED_WHITELIST` 零測試覆蓋＝豁免路徑（ADR 0077 第 3 項）壞掉無信號。

        突變實證：外層面兩處白名單略過分支（工作樹面與 staged 面）整段刪除後全套仍全綠。
        本案一次釘住兩處——白名單生效時兩面皆須零 finding，任一分支被刪即有一面重新報紅。
        """
        with tempfile.TemporaryDirectory() as d:
            self._outer(d)
            self._write(d, "docs/sample.md", "k='" + self.RED["aws-akia"] + "'\n")
            self._g(d, "add", "docs/sample.md")
            before = [x for x in lint_cred_outer(d) if x["level"] == ERROR]
            self.assertEqual(len(before), 1, msg=str(before))   # 白名單外＝報紅
            self.assertEqual(
                self._with_whitelist(("docs/sample.md",), lambda: lint_cred_outer(d)), [])
            after = [x for x in lint_cred_outer(d) if x["level"] == ERROR]
            self.assertEqual(len(after), 1, msg=str(after))     # 還原後恢復報紅

    def test_self_test_catches_dead_patterns(self):
        """樣式集被改壞成永不命中（恆綠）→self-test 逐 label 報 ERROR。"""
        dead = (("pem-private-key", re.compile(r"ZZZ-NEVER-MATCH-ZZZ")),)
        f = self._with_patterns(dead, cred_self_test)
        self.assertEqual(len(f), 4)
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertEqual({lbl for lbl in self.RED for x in f if lbl in x["msg"]}, set(self.RED))

    def test_self_test_catches_overbroad_patterns(self):
        """樣式集被改到過寬→綠樣本誤報、self-test 同樣報 ERROR。"""
        wide = (("pem-private-key", re.compile(r".")),)
        f = self._with_patterns(wide, cred_self_test)
        self.assertTrue(f)
        self.assertTrue(all(x["level"] == ERROR for x in f))
        self.assertTrue(any("綠樣本" in x["msg"] for x in f))


SNAP_COLS = [
    {"table": "sys_user", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": None},
    {"table": "sys_user", "column": "user_name", "ordinal": 2,
     "type": "character varying(64)", "nullable": False, "default": None},
    {"table": "casbin_rule", "column": "id", "ordinal": 1, "type": "bigint",
     "nullable": False, "default": "nextval('casbin_rule_id_seq'::regclass)"},
]
SNAP_IDX = [
    {"table": "sys_user", "name": "sys_user_pkey",
     "definition": "CREATE UNIQUE INDEX sys_user_pkey ON public.sys_user USING btree (id)"},
    {"table": "casbin_rule", "name": "casbin_rule_pkey",
     "definition": "CREATE UNIQUE INDEX casbin_rule_pkey ON public.casbin_rule USING btree (id)"},
]
SNAP_CONS = [
    {"table": "sys_user", "name": "sys_user_pkey", "definition": "PRIMARY KEY (id)"},
]
ACC_USERS = [
    {"id": 5, "user_name": "Admin", "nick_name": "Admin", "status": 1},
    {"id": 4, "user_name": "Super", "nick_name": "Super", "status": 1},
]
ACC_ROLES = [
    {"id": 5, "role_code": "R_ADMIN", "role_name": "管理員", "status": 1},
    {"id": 4, "role_code": "R_SUPER", "role_name": "超管", "status": 1},
]
ACC_BINDS = [{"user_id": 5, "role_id": 5}, {"user_id": 4, "role_id": 4}]


def _fake_fetch(sql, root=None):
    """測試用 fetch：依 SQL 內容回對應 canned rows（sys_user_role 判在 sys_user 前）。"""
    if "information_schema.columns" in sql:
        return list(SNAP_COLS)
    if "pg_indexes" in sql:
        return list(SNAP_IDX)
    if "pg_constraint" in sql:
        return list(SNAP_CONS)
    if "sys_user_role" in sql:
        return list(ACC_BINDS)
    if "sys_user" in sql:
        return list(ACC_USERS)
    if "sys_role" in sql:
        return list(ACC_ROLES)
    raise AssertionError("未知 SQL：" + sql)


class TestSnapshot(unittest.TestCase):
    """T015：refresh 快照面——確定性排序、密碼欄排除、缺 stack fail-loud、原子替換。"""

    def test_schema_snapshot_sorted_and_deterministic(self):
        a = snapshot_dumps(build_schema_snapshot(SNAP_COLS, SNAP_IDX, SNAP_CONS))
        b = snapshot_dumps(build_schema_snapshot(
            list(reversed(SNAP_COLS)), list(reversed(SNAP_IDX)), list(reversed(SNAP_CONS))))
        self.assertEqual(a, b)                       # 入序無關、同 byte
        snap = json.loads(a)
        self.assertEqual(set(snap), {"columns", "indexes", "constraints"})  # 無產生時點欄位
        self.assertEqual([c["table"] for c in snap["columns"]],
                         ["casbin_rule", "sys_user", "sys_user"])            # 表名序
        self.assertEqual([c["ordinal"] for c in snap["columns"][1:]], [1, 2])  # ordinal 序
        self.assertEqual([i["name"] for i in snap["indexes"]],
                         ["casbin_rule_pkey", "sys_user_pkey"])

    def test_schema_snapshot_excludes_seaql_migrations(self):
        cols = SNAP_COLS + [{"table": "seaql_migrations", "column": "version", "ordinal": 1,
                             "type": "character varying", "nullable": False, "default": None}]
        idx = SNAP_IDX + [{"table": "seaql_migrations", "name": "seaql_migrations_pkey",
                           "definition": "CREATE UNIQUE INDEX …"}]
        text = snapshot_dumps(build_schema_snapshot(cols, idx, SNAP_CONS))
        self.assertNotIn("seaql_migrations", text)

    def test_schema_snapshot_bad_row_shape_fail_loud(self):
        with self.assertRaises(SnapshotError):
            build_schema_snapshot([{"table": "t", "column": "c"}], [], [])  # 缺欄

    def test_accounts_snapshot_password_excluded_fail_loud(self):
        bad = dict(ACC_USERS[0])
        bad["password"] = "$argon2id$假雜湊"
        with self.assertRaises(SnapshotError) as cm:
            build_accounts_snapshot([bad], ACC_ROLES, ACC_BINDS)
        self.assertIn("password", str(cm.exception))
        text = snapshot_dumps(build_accounts_snapshot(ACC_USERS, ACC_ROLES, ACC_BINDS))
        self.assertNotIn("password", text)
        self.assertNotIn("argon2", text)

    def test_accounts_snapshot_sorted_and_deterministic(self):
        a = snapshot_dumps(build_accounts_snapshot(ACC_USERS, ACC_ROLES, ACC_BINDS))
        b = snapshot_dumps(build_accounts_snapshot(
            list(reversed(ACC_USERS)), list(reversed(ACC_ROLES)), list(reversed(ACC_BINDS))))
        self.assertEqual(a, b)
        snap = json.loads(a)
        self.assertEqual(set(snap), {"users", "roles", "bindings"})
        self.assertEqual([u["id"] for u in snap["users"]], [4, 5])
        self.assertEqual([r["id"] for r in snap["roles"]], [4, 5])
        self.assertEqual([x["user_id"] for x in snap["bindings"]], [4, 5])

    def test_atomic_write_no_leftover_tmp(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "x.json")
            _atomic_write(p, "第一版\n")
            _atomic_write(p, "第二版\n")
            with open(p, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "第二版\n")
            self.assertEqual(os.listdir(os.path.join(d, "sub")), ["x.json"])  # 無殘留暫存檔

    def test_refresh_writes_both_snapshots_byte_identical_rerun(self):
        with tempfile.TemporaryDirectory() as d, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cmd_refresh(root=d, fetch=_fake_fetch), 0)
            p_schema = os.path.join(d, "docs/ops/reference-src/schema-snapshot.json")
            p_accounts = os.path.join(d, "docs/ops/reference-src/accounts-snapshot.json")
            with open(p_schema, encoding="utf-8") as fh:
                schema1 = fh.read()
            with open(p_accounts, encoding="utf-8") as fh:
                accounts1 = fh.read()
            self.assertEqual(set(json.loads(schema1)), {"columns", "indexes", "constraints"})
            self.assertEqual(set(json.loads(accounts1)), {"users", "roles", "bindings"})
            self.assertEqual(cmd_refresh(root=d, fetch=_fake_fetch), 0)  # 同庫重跑
            with open(p_schema, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), schema1)                     # byte-identical
            with open(p_accounts, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), accounts1)

    def test_refresh_no_partial_write_on_late_failure(self):
        calls = {"n": 0}

        def flaky(sql, root=None):
            calls["n"] += 1
            if calls["n"] >= 4:                      # 帳號面撈取才失敗
                raise SnapshotError("psql 撈取失敗（模擬）")
            return []

        with tempfile.TemporaryDirectory() as d, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SnapshotError):
                cmd_refresh(root=d, fetch=flaky)
            self.assertFalse(os.path.exists(os.path.join(d, "docs/ops/reference-src")))

    def test_psql_fetch_stack_down_fail_loud(self):
        class Down:
            returncode = 1
            stdout = ""
            stderr = 'service "postgres" is not running'

        with self.assertRaises(SnapshotError) as cm:
            psql_fetch("SELECT 1", root=".", run=lambda *a, **k: Down())
        self.assertIn(STACK_HINT, str(cm.exception))
        self.assertIn("postgres", str(cm.exception))

    def test_psql_fetch_docker_missing_fail_loud(self):
        def boom(*a, **k):
            raise OSError("No such file or directory: 'docker'")

        with self.assertRaises(SnapshotError) as cm:
            psql_fetch("SELECT 1", root=".", run=boom)
        self.assertIn(STACK_HINT, str(cm.exception))

    def test_cli_refresh_without_docker_exits_nonzero_with_hint(self):
        env = dict(os.environ, PATH=os.devnull)      # docker 不可得
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "refresh"],
                           capture_output=True, encoding="utf-8", errors="replace", env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("up -d --wait", r.stderr)      # 提示啟動命令


class TestSnapshotReference(unittest.TestCase):
    """T017：generate／check 兩來源——快照→兩表、確定性、轉真、L2 分流、缺檔 fail-loud。"""

    ARCH = {
        "sys_user": {"table": "sys_user", "variant": "A", "label": "A 業務全六欄"},
        "casbin_rule": {"table": "casbin_rule", "variant": "D", "label": "D 治理"},
    }

    def _schema_snap(self):
        return build_schema_snapshot(SNAP_COLS, SNAP_IDX, SNAP_CONS)

    def _accounts_snap(self):
        return build_accounts_snapshot(ACC_USERS, ACC_ROLES, ACC_BINDS)

    def test_gen_reference_schema_sections_and_archetype(self):
        text = gen_reference_schema(self._schema_snap(), self.ARCH)
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertLess(text.index("## casbin_rule"), text.index("## sys_user"))  # 表名序分節
        self.assertIn("A 業務全六欄", text)          # archetype 變體歸屬標註
        self.assertIn("D 治理", text)
        self.assertIn("| user_name | character varying(64) |", text)  # 欄明細列
        self.assertIn("sys_user_pkey", text)         # 索引／約束清單入表

    def test_gen_reference_schema_deterministic_same_bytes(self):
        a = gen_reference_schema(self._schema_snap(), self.ARCH)
        b = gen_reference_schema(
            build_schema_snapshot(list(reversed(SNAP_COLS)), list(reversed(SNAP_IDX)),
                                  list(reversed(SNAP_CONS))),
            dict(reversed(list(self.ARCH.items()))))
        self.assertEqual(a, b)

    def test_gen_reference_schema_missing_archetype_fail_loud(self):
        arch = {"sys_user": self.ARCH["sys_user"]}   # 缺 casbin_rule 歸屬
        with self.assertRaises(SnapshotError) as cm:
            gen_reference_schema(self._schema_snap(), arch)
        self.assertIn("casbin_rule", str(cm.exception))

    def test_gen_reference_accounts_bindings_and_zero_password(self):
        text = gen_reference_accounts(self._accounts_snap())
        self.assertTrue(text.startswith(GEN_HEADER))
        self.assertIn("| Super | Super | 1 | R_SUPER |", text)   # 帳號｜暱稱｜狀態｜角色綁定
        self.assertIn("| Admin | Admin | 1 | R_ADMIN |", text)
        self.assertNotIn("password", text)
        self.assertNotIn("argon2", text)

    def test_gen_reference_accounts_dangling_binding_fail_loud(self):
        snap = self._accounts_snap()
        snap["bindings"].append({"user_id": 4, "role_id": 99})
        with self.assertRaises(SnapshotError):
            gen_reference_accounts(snap)

    def test_reference_live_schema_accounts_promoted(self):
        self.assertIn("schema", REFERENCE_LIVE)
        self.assertIn("accounts", REFERENCE_LIVE)
        self.assertIn("screens", REFERENCE_LIVE)
        text = gen_state(TestGenState.CTX)
        state_lines = {name: line
                       for line in text.splitlines()
                       for name in ("routes", "ports", "schema", "accounts", "screens")
                       if line.startswith(f"- reference/{name}：")}
        # screens 轉真後、五表全為真表、無殘餘 stub
        for name in ("schema", "accounts", "screens"):
            self.assertNotIn("stub", state_lines[name], msg=name)   # 轉真
            self.assertIn("generate", state_lines[name], msg=name)

    def test_check_reports_schema_accounts_drift_as_l2(self):
        for base in ("schema", "accounts"):
            with tempfile.TemporaryDirectory() as root:
                os.makedirs(os.path.join(root, "docs/generated/reference"))
                rel = f"docs/generated/reference/{base}.md"
                with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                    fh.write("舊表\n")
                f = check_generated(root, {rel: "新表\n"})
                self.assertEqual(len(f), 1, msg=base)
                self.assertEqual(f[0]["code"], "L2", msg=base)      # L2 分流（指名來源側）
                self.assertIn(f"{base}-snapshot.json", f[0]["msg"], msg=base)

    def _write_reference_src(self, root, schema=True, accounts=True, amap=True):
        d = os.path.join(root, REFERENCE_SRC_DIR)
        os.makedirs(d)
        if schema:
            with open(os.path.join(root, SCHEMA_SNAPSHOT), "w", encoding="utf-8") as fh:
                fh.write(snapshot_dumps(self._schema_snap()))
        if accounts:
            with open(os.path.join(root, ACCOUNTS_SNAPSHOT), "w", encoding="utf-8") as fh:
                fh.write(snapshot_dumps(self._accounts_snap()))
        if amap:
            with open(os.path.join(root, ARCHETYPE_MAP), "w", encoding="utf-8") as fh:
                json.dump({"tables": list(self.ARCH.values())}, fh, ensure_ascii=False)

    def test_compute_snapshot_reference_green_and_deterministic(self):
        with tempfile.TemporaryDirectory() as root:
            self._write_reference_src(root)
            files = compute_snapshot_reference(root)
            self.assertEqual(set(files), {"docs/generated/reference/schema.md",
                                          "docs/generated/reference/accounts.md"})
            self.assertEqual(files, compute_snapshot_reference(root))  # 同快照同 byte

    def test_compute_snapshot_reference_missing_snapshot_fail_loud(self):
        with tempfile.TemporaryDirectory() as root:
            self._write_reference_src(root, schema=False)
            with self.assertRaises(SnapshotError) as cm:
                compute_snapshot_reference(root)
            self.assertIn("schema-snapshot.json", str(cm.exception))
            self.assertIn("refresh", str(cm.exception))              # 提示補救命令

    def test_compute_snapshot_reference_missing_archetype_map_fail_loud(self):
        with tempfile.TemporaryDirectory() as root:
            self._write_reference_src(root, amap=False)
            with self.assertRaises(SnapshotError) as cm:
                compute_snapshot_reference(root)
            self.assertIn("archetype-map.json", str(cm.exception))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "test":
        result = unittest.main(argv=[argv[0]], exit=False, verbosity=1).result
        return 0 if result.wasSuccessful() else 1
    try:
        if cmd == "lint":
            return cmd_lint()
        if cmd == "generate":
            return cmd_generate()
        if cmd == "check":
            return cmd_check()
        if cmd == "refresh":
            return cmd_refresh()
        if cmd == "errata":
            if len(argv) < 3:
                print("用法：tools/docs-sync.py errata <關鍵詞>", file=sys.stderr)
                return 2
            return cmd_errata(argv[2])
    except UnicodeDecodeError as ex:
        print(f"[ERROR] 編碼｜文件含非 UTF-8 內容（{ex}）——fail-closed，修復編碼後重跑",
              file=sys.stderr)
        return 1
    except ComposePortsError as ex:
        print(f"[ERROR] ports 解析｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except RouterRoutesError as ex:
        print(f"[ERROR] routes 解析｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except ElegantRoutesError as ex:
        print(f"[ERROR] screens 解析｜{ex}——fail-loud，處置後重跑", file=sys.stderr)
        return 1
    except SnapshotError as ex:
        print(f"[ERROR] 快照管線｜{ex}", file=sys.stderr)
        return 1
    print(f"未知子命令：{cmd}", file=sys.stderr)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
