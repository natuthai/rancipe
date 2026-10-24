#!/usr/bin/env python3
"""ตรวจไฟล์ข้อมูลใน data/ ก่อน commit

ใช้: python3 scripts/validate_data.py
ใช้แค่ Python มาตรฐาน ไม่ต้องติดตั้งอะไรเพิ่ม
จบด้วยรหัส 1 ถ้ามี ERROR (WARN ไม่ทำให้ล้ม)
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DIFFICULTIES = {"ง่าย", "กลาง", "ยาก"}
REQUIRED = ["id", "menu_name", "category", "main_ingredients", "instructions", "cook_time", "difficulty"]

errors, warns = [], []


def read(name):
    path = DATA / name
    if not path.exists():
        errors.append(f"{name}: ไม่พบไฟล์")
        return [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        return rows, (rows[0].keys() if rows else [])


recipes, cols = read("recipes.csv")
categories, _ = read("categories.csv")
aliases, _ = read("ingredient_aliases.csv")

for c in REQUIRED:
    if recipes and c not in cols:
        errors.append(f"recipes.csv: ไม่มีคอลัมน์ {c}")

cat_names = {r["category"].strip() for r in categories}
ids = Counter(r.get("id", "").strip() for r in recipes)
names = Counter(r.get("menu_name", "").strip() for r in recipes)

for i, r in enumerate(recipes, start=2):  # แถวที่ 2 = แถวแรกของข้อมูล
    who = f"recipes.csv แถว {i} ({r.get('menu_name', '').strip() or r.get('id', '').strip() or 'ไม่มีชื่อ'})"
    for c in REQUIRED:
        if not r.get(c, "").strip():
            errors.append(f"{who}: ช่อง {c} ว่าง")
    rid = r.get("id", "").strip()
    if rid and ids[rid] > 1:
        errors.append(f"{who}: id ซ้ำ ({rid})")
    name = r.get("menu_name", "").strip()
    if name and names[name] > 1:
        warns.append(f"{who}: ชื่อเมนูซ้ำ")
    cat = r.get("category", "").strip()
    if cat and cat_names and cat not in cat_names:
        errors.append(f"{who}: หมวด '{cat}' ไม่อยู่ใน categories.csv")
    diff = r.get("difficulty", "").strip()
    if diff and diff not in DIFFICULTIES:
        errors.append(f"{who}: ความยาก '{diff}' ต้องเป็น {', '.join(sorted(DIFFICULTIES))}")
    ct = r.get("cook_time", "").strip()
    if ct and not re.search(r"\d+", ct):
        errors.append(f"{who}: cook_time '{ct}' ไม่มีตัวเลขนาที")
    for c in ("main_ingredients", "optional_ingredients", "tags"):
        parts = [p.strip() for p in re.split(r"[,，、]", r.get(c, "")) if p.strip()]
        dup = [p for p, n in Counter(parts).items() if n > 1]
        if dup:
            warns.append(f"{who}: {c} มีค่าซ้ำ {', '.join(dup)}")

seen = {}
for i, a in enumerate(aliases, start=2):
    canon = a.get("canonical_ingredient", "").strip()
    if not canon:
        errors.append(f"ingredient_aliases.csv แถว {i}: canonical_ingredient ว่าง")
        continue
    for w in (x.strip() for x in a.get("alias_words", "").split(",") if x.strip()):
        if w in seen and seen[w] != canon:
            warns.append(f"ingredient_aliases.csv: '{w}' เป็นชื่อเรียกของทั้ง '{seen[w]}' และ '{canon}'")
        seen[w] = canon

for w in warns:
    print("WARN ", w)
for e in errors:
    print("ERROR", e)
print(f"\nตรวจ {len(recipes)} เมนู, {len(categories)} หมวด, {len(aliases)} กลุ่มชื่อเรียก — "
      f"{len(errors)} error, {len(warns)} warning")
sys.exit(1 if errors else 0)
