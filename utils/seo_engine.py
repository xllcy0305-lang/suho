# -*- coding: utf-8 -*-
"""SEO 标题生成引擎 — 采样优化 + 去重 + AI 评分 + 硬迭代上限"""

import random
import itertools
import logging

from config import TARGET_TITLE_COUNT, MAX_SAMPLE_COMBOS, CN_QUALITIES, CN_FEATURES, THAI_PLATFORMS, CN_PLATFORMS

logger = logging.getLogger(__name__)

# 硬迭代上限：防止 Streamlit 因循环过长而卡死
MAX_ITERATIONS = 50000


def _sample(pool: list, max_items: int) -> list:
    if len(pool) <= max_items:
        return pool
    return random.sample(pool, max_items)


def _ai_score(title: str) -> int:
    score = 50
    if 30 <= len(title) <= 80:
        score += 15
    elif len(title) > 100:
        score -= 10
    if any(c.isdigit() for c in title):
        score += 10
    promo = ("ขายดี", "ราคาถูก", "ลดราคา", "พร้อมส่ง", "100%", "高品质", "热销", "特价")
    if any(w in title for w in promo):
        score += 8
    if any(kw in title for kw in ("IP68", "Bluetooth", "SPF", "4K", "USB", "PD")):
        score += 7
    return min(100, max(0, score))


def generate_thai_titles(cat_data: dict, max_chars: int, count: int = TARGET_TITLE_COUNT) -> list[dict]:
    bases = cat_data.get("base", [])
    mats = cat_data.get("material_specs", [])
    scenes = cat_data.get("scene_audience", [])
    lts = cat_data.get("longtail", [])

    if not bases or not lts:
        return []

    titles_set: set[str] = set()
    sample_limit = int((MAX_SAMPLE_COMBOS / max(len(bases), 1)) ** 0.66)
    s_mats = _sample(mats, sample_limit)
    s_scenes = _sample(scenes, sample_limit) if scenes else []
    iters = 0

    if s_scenes:
        for b, m, s, l in itertools.product(bases, s_mats, s_scenes, lts):
            t = f"{b} {m} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and iters < MAX_ITERATIONS:
        for b, m, l in itertools.product(bases, s_mats, lts):
            t = f"{b} {m} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and iters < MAX_ITERATIONS:
        s_sc2 = _sample(scenes, sample_limit)
        for b, s, l in itertools.product(bases, s_sc2, lts):
            t = f"{b} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and iters < MAX_ITERATIONS:
        for b, l in itertools.product(bases, lts):
            t = f"{b} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    result = list(titles_set)
    random.shuffle(result)
    return [{"title": t, "chars": len(t), "score": _ai_score(t)} for t in result[:count]]


def generate_cn_titles(cat_data: dict, product_cn: str, max_chars: int,
                        count: int = TARGET_TITLE_COUNT) -> list[dict]:
    mats = cat_data.get("material_specs", [])
    if not mats:
        return []

    templates = [
        lambda m, q, f: f"{product_cn} {m} {q} {f}",
        lambda m, q, f: f"{product_cn} {q} {f} {m}",
        lambda m, q, f: f"{q}{product_cn} {f} {m}",
        lambda m, q, f: f"{product_cn}{f} {m} {q}",
        lambda m, q, f: f"{product_cn} {m} {f}",
        lambda m, q, f: f"{q}{product_cn} {f}",
        lambda m, q, f: f"{product_cn} {f} {q}",
    ]

    s_mats = _sample(mats, 5)
    titles_set: set[str] = set()
    iters = 0

    for tpl in templates:
        for m, q, f in itertools.product(s_mats, CN_QUALITIES, CN_FEATURES):
            t = tpl(m, q, f)
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 2 or iters >= MAX_ITERATIONS:
                break
        if len(titles_set) >= count or iters >= MAX_ITERATIONS:
            break

    result = list(titles_set)
    random.shuffle(result)
    return [{"title": t, "chars": len(t), "score": _ai_score(t)} for t in result[:count]]


def dispatch(product_cn: str, plat_key: str, cat_data: dict, max_chars: int) -> list[dict]:
    if plat_key in THAI_PLATFORMS:
        return generate_thai_titles(cat_data, max_chars)
    if plat_key in CN_PLATFORMS:
        return generate_cn_titles(cat_data, product_cn, max_chars)
    return []
