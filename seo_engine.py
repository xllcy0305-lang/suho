# -*- coding: utf-8 -*-
"""SEO 标题生成引擎 v2 — 8 平台差异化模板 + AI 评分"""

import random
import logging

from config import (
    TARGET_TITLE_COUNT, PLATFORM_LIMITS,
    CN_QUALITIES, CN_FEATURES,
    CN_TIKTOK_HOT, CN_TAOBAO_HOT, CN_PDD_HOT, CN_DOUYIN_HOT, CN_EMOTIONS,
)

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 30000

# 通用英文词库（所有类目共享，用于 TEMU / Amazon）
EN_MATERIALS = [
    "Premium Quality", "High-Density", "Lightweight", "Heavy-Duty",
    "Waterproof", "Anti-Slip", "Durable", "Foldable", "Portable",
    "Stainless Steel", "Aluminum Alloy", "Oxford Fabric", "Canvas",
    "Eco-Friendly", "Non-Toxic", "BPA-Free", "Food Grade",
]
EN_SCENES = [
    "Outdoor", "Indoor", "Camping", "Travel", "Home", "Office",
    "Kitchen", "Bathroom", "Garden", "Sports", "Gym", "Beach",
    "Hiking", "Picnic", "Backyard", "Living Room",
]
EN_FEATURES = [
    "Easy to Install", "Space Saving", "Quick Fold", "Multi-Purpose",
    "Ergonomic Design", "Adjustable", "Large Capacity", "Ultra-Light",
    "All-Season", "Professional Grade", "Military Grade", "Travel-Friendly",
]
EN_CONVERT = [
    "Free Shipping", "Best Seller", "New Arrival", "Hot Deal",
    "Limited Offer", "Top Rated", "Customer Favorite", "Value Pack",
    "Flash Sale", "Clearance", "Premium Selection", "Exclusive",
]

# ═══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════════

def _sample(pool: list, n: int) -> list:
    if len(pool) <= n:
        return pool
    return random.sample(pool, n)


def _field(cat_data: dict, key: str, fallback: str = "") -> list:
    """取类目字段，兼容新旧格式"""
    return cat_data.get(key) or (cat_data.get(fallback) if fallback else []) or []


def _pick(product_cn: str, cat_data: dict) -> dict:
    """组装生成所需的各语种词库"""
    subs = cat_data.get("subcategories", [])
    bases_raw = cat_data.get("base", {})

    # 找到子类目索引，从平台 base 取对应词
    idx = -1
    for i, s in enumerate(subs):
        if s == product_cn or s in product_cn or product_cn in s:
            idx = i
            break

    def _base(platform: str) -> list:
        if isinstance(bases_raw, dict):
            b = bases_raw.get(platform, [])
            if idx >= 0 and idx < len(b):
                return [b[idx]]
            return b[:3] if b else []
        return [product_cn]

    mats = _field(cat_data, "material_specs")
    scenes = _field(cat_data, "scene_keywords")
    longtails = _field(cat_data, "longtail_keywords")

    return {
        "shopee": _base("shopee"),
        "lazada": _base("lazada"),
        "tiktok": _base("tiktok"),
        "temu": _base("temu"),
        "amazon": _base("amazon"),
        "taobao": _base("taobao"),
        "pinduoduo": _base("pinduoduo"),
        "douyin": _base("douyin"),
        "mats": mats,
        "scenes": scenes,
        "longtails": longtails,
        "shopee_hot": _field(cat_data, "shopee_hot"),
        "lazada_hot": _field(cat_data, "lazada_hot"),
        "tiktok_hot": _field(cat_data, "tiktok_hot"),
        "temu_hot": _field(cat_data, "temu_hot"),
        "cn_scenes": _field(cat_data, "cn_scene_keywords"),
        "cn_tb_hot": _field(cat_data, "cn_taobao_hot"),
        "cn_pd_hot": _field(cat_data, "cn_pdd_hot"),
        "cn_dy_hot": _field(cat_data, "cn_douyin_hot"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AI 评分（平台感知）
# ═══════════════════════════════════════════════════════════════════════════════

def _ai_score(title: str, platform: str, min_c: int, max_c: int) -> int:
    score = 40
    length = len(title)
    ratio = length / max(max_c, 1)

    # 填充率 60-95% 最佳
    if 0.6 <= ratio <= 0.95:
        score += 20
    elif ratio > 0.95:
        score += 10
    elif ratio < 0.4:
        score -= 10

    # 有数字加分
    if any(c.isdigit() for c in title):
        score += 8

    # 重复词惩罚
    words = title.split()
    if len(words) != len(set(words)):
        score -= 15

    # 平台专属加分
    if platform in ("shopee_th", "lazada_th"):
        thai_promo = ("ขายดี", "ราคาถูก", "พร้อมส่ง", "ของแท้", "ส่งฟรี",
                      "LazMall", "Flash Sale", "ลดราคา")
        if any(w in title for w in thai_promo):
            score += 10
    elif platform in ("temu", "amazon"):
        en_promo = ("Free Shipping", "Best Seller", "New Arrival", "Hot Deal",
                    "Premium", "Professional")
        if any(w in title for w in en_promo):
            score += 10
    elif platform == "tiktok_global":
        if any(w in title for w in CN_TIKTOK_HOT):
            score += 12
    elif platform == "taobao":
        if any(w in title for w in CN_TAOBAO_HOT):
            score += 10
    elif platform == "pinduoduo":
        if any(w in title for w in CN_PDD_HOT):
            score += 10
    elif platform == "douyin":
        if any(w in title for w in CN_DOUYIN_HOT):
            score += 12

    # 规格词加分
    spec_words = ("IP68", "Bluetooth", "SPF", "4K", "USB", "PD", "mAh",
                  "防水", "蓝牙", "不锈钢", "铝合金", "有机", "无糖")
    if any(w in title for w in spec_words):
        score += 7

    return min(100, max(0, score))


def _make_result(titles_set: set, platform: str, min_c: int, max_c: int,
                 count: int) -> list[dict]:
    """去重、打分、排序、取 top N"""
    result = []
    for t in titles_set:
        result.append({"title": t, "chars": len(t),
                       "score": _ai_score(t, platform, min_c, max_c)})
    result.sort(key=lambda x: x["score"], reverse=True)
    return result[:count]


# ═══════════════════════════════════════════════════════════════════════════════
# Shopee 泰国站 — 泰语，关键词堆叠搜索优化
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_shopee(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    bases = info["shopee"]
    mats = info["mats"]
    scenes = info["scenes"]
    lts = info["longtails"]
    hot = info["shopee_hot"]
    if not bases:
        return []

    min_c = PLATFORM_LIMITS["shopee_th"]["min_chars"]
    limit = max(4, int(2000 / max(len(bases), 1)))
    s_mats = _sample(mats, limit)
    s_scenes = _sample(scenes, limit)
    s_lts = _sample(lts, limit)
    seen: set[str] = set()
    iters = 0

    # 模板: base + material + scene + hot/longtail
    for b in bases:
        for m in s_mats:
            for s in s_scenes:
                for h in hot:
                    t = f"{b} {m} {s} {h}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                for l in s_lts:
                    t = f"{b} {m} {s} {l}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break
            if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                break
        # base + hot + longtail 补充
        for h in hot:
            for l in s_lts:
                t = f"{b} {h} {l}"
                if 1 <= len(t) <= max_chars:
                    seen.add(t)
                iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break

    return _make_result(seen, "shopee_th", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# Lazada 泰国站 — 泰语，LazMall 官方店铺风格
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_lazada(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    bases = info["lazada"]
    mats = info["mats"]
    scenes = info["scenes"]
    lts = info["longtails"]
    hot = info["lazada_hot"]
    if not bases:
        return []

    min_c = PLATFORM_LIMITS["lazada_th"]["min_chars"]
    limit = max(4, int(2000 / max(len(bases), 1)))
    s_mats = _sample(mats, limit)
    s_scenes = _sample(scenes, limit)
    s_lts = _sample(lts, limit)
    seen: set[str] = set()
    iters = 0

    # 模板: base + material + scene + hot/longtail (4词组合)
    for b in bases:
        for m in s_mats:
            for s in s_scenes:
                for h in hot:
                    t = f"{b} {m} {s} {h}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                for l in s_lts:
                    t = f"{b} {m} {s} {l}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break
            for l in s_lts:
                t = f"{b} {m} {l}"
                if 1 <= len(t) <= max_chars:
                    seen.add(t)
                iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break
            if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    return _make_result(seen, "lazada_th", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# TikTok 海外 — 中文短标题，病毒式传播
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_tiktok(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    bases = info["tiktok"]
    hot = info["tiktok_hot"]
    scenes = info["cn_scenes"]
    features = CN_FEATURES
    emotions = CN_EMOTIONS
    if not bases:
        bases = [product_cn]

    min_c = PLATFORM_LIMITS["tiktok_global"]["min_chars"]
    seen: set[str] = set()
    iters = 0

    templates = [
        # 爆款月亮椅｜露营氛围感神器
        lambda b, h, s: f"{h}{b}｜{s}",
        # 月亮椅 绝绝子 太好用了
        lambda b, h, s: f"{b} {h}",
        # 这个折叠椅也太好用了吧
        lambda b, e, f: f"{e}的{b}，{f}",
        # 月亮椅｜户外必备神器
        lambda b, h, f: f"{b}｜{h} {f}",
        # 姐妹们冲！月亮椅真的绝了
        lambda b, h, e: f"{h}！{b}{e}",
    ]

    for b in bases:
        for h in hot:
            for s in scenes:
                for tpl in templates[:2]:
                    t = tpl(b, h, s)
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                    break
            for e in emotions:
                for tpl in templates[2:]:
                    t = tpl(b, h, e)
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                    break
            if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                break

    return _make_result(seen, "tiktok_global", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMU — 英语长标题，关键词堆叠 + 转化词
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_temu(product_cn: str, cat_data: dict, max_chars: int,
              count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    bases = info["temu"]
    if not bases:
        return []

    min_c = PLATFORM_LIMITS["temu"]["min_chars"]
    mats = _sample(EN_MATERIALS, 6)
    scenes = _sample(EN_SCENES, 6)
    feats = _sample(EN_FEATURES, 6)
    convs = _sample(EN_CONVERT, 4)
    seen: set[str] = set()
    iters = 0

    for b in bases:
        # Product + Material + Scene + Feature + Conversion
        for m in mats:
            for s in scenes:
                for f in feats:
                    t = f"{b} {m} {s} {f}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                for c in convs:
                    t = f"{b} {m} {s} {c}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break
            for f in feats:
                for c in convs:
                    t = f"{b} {m} {f} {c}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break
            if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    return _make_result(seen, "temu", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# Amazon — 英语，专业标题结构 [Brand] + Type + Keyword + Function + Spec
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_amazon(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    bases = info["amazon"]
    if not bases:
        return []

    min_c = PLATFORM_LIMITS["amazon"]["min_chars"]
    mats = _sample(EN_MATERIALS, 6)
    scenes = _sample(EN_SCENES, 6)
    feats = _sample(EN_FEATURES, 6)
    seen: set[str] = set()
    iters = 0

    # Amazon 模板: Type + Material + Feature + Scene
    for b in bases:
        for m in mats:
            for f in feats:
                t = f"{b} {m} {f}"
                if 1 <= len(t) <= max_chars:
                    seen.add(t)
                iters += 1
            for s in scenes:
                t = f"{b} {m} {s}"
                if 1 <= len(t) <= max_chars:
                    seen.add(t)
                iters += 1
            if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                break
        for s in scenes:
            for f in feats:
                t = f"{b} {s} {f}"
                if 1 <= len(t) <= max_chars:
                    seen.add(t)
                iters += 1
                if len(seen) >= count * 3 or iters >= MAX_ITERATIONS:
                    break

    return _make_result(seen, "amazon", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# 淘宝 — 中文短标题 40-60 字，品质词 + 特性 + 场景
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_taobao(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    subs = cat_data.get("subcategories", [])
    scenes = info["cn_scenes"]
    hot = info["cn_tb_hot"]
    features = CN_FEATURES
    min_c = PLATFORM_LIMITS["taobao"]["min_chars"]
    seen: set[str] = set()
    iters = 0

    # 用子类目扩展产品词
    extended_bases = [product_cn]
    for s in subs:
        if s != product_cn and len(s) >= 2:
            extended_bases.append(s)

    # 模板: 产品词 + 子类目 + 品质 + 特性 + 场景 + 营销 (无空格拼接)
    for b in extended_bases:
        prefix = b if b != product_cn else product_cn
        for q in CN_QUALITIES:
            for f1 in features:
                for f2 in features:
                    if f2 == f1:
                        continue
                    t = f"{prefix}{q}{f1}{f2}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                for s in scenes:
                    t = f"{prefix}{q}{f1}{s}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                for h in hot:
                    t = f"{product_cn}{q}{f1}{h}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                    break
            if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                break
        if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
            break

    return _make_result(seen, "taobao", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# 拼多多 — 中文标题 60-120 字，价格导向 + 厂家直销
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_pdd(product_cn: str, cat_data: dict, max_chars: int,
             count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    subs = cat_data.get("subcategories", [])
    scenes = info["cn_scenes"]
    hot = info["cn_pd_hot"]
    features = CN_FEATURES
    min_c = PLATFORM_LIMITS["pinduoduo"]["min_chars"]
    seen: set[str] = set()
    iters = 0

    # 用子类目扩展
    extended = [product_cn] + [s for s in subs if s != product_cn and len(s) >= 2]

    # 模板: 产品+子类目+特性+品质+营销 (4-5 词无空格拼接)
    for b in extended[:3]:
        prefix = b if b != product_cn else product_cn
        for q in CN_QUALITIES:
            for f in features:
                for h in hot:
                    t = f"{prefix}{q}{f}{h}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                    if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                        break
                for s in scenes:
                    t = f"{prefix}{q}{f}{s}"
                    if 1 <= len(t) <= max_chars:
                        seen.add(t)
                    iters += 1
                if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                    break
            if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
                break
        if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
            break

    return _make_result(seen, "pinduoduo", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# 抖音 — 中文超短标题 20-55 字，情绪化 + 病毒式
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_douyin(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    info = _pick(product_cn, cat_data)
    scenes = info["cn_scenes"]
    hot = info["cn_dy_hot"]
    features = CN_FEATURES
    emotions = CN_EMOTIONS
    min_c = PLATFORM_LIMITS["douyin"]["min_chars"]
    seen: set[str] = set()
    iters = 0

    # 抖音短标题：多词拼接达到 min_chars
    for h1 in hot:
        for h2 in hot:
            if h2 == h1:
                continue
            t = f"{h1}！{product_cn}{h2}"
            if 1 <= len(t) <= max_chars:
                seen.add(t)
            iters += 1
        for f in features:
            t = f"{product_cn}{f}{h1}"
            if 1 <= len(t) <= max_chars:
                seen.add(t)
            iters += 1
        for e in emotions:
            t = f"{e}的{product_cn}"
            if 1 <= len(t) <= max_chars:
                seen.add(t)
            iters += 1
        for s in scenes:
            t = f"{product_cn}{s}必备{h1}"
            if 1 <= len(t) <= max_chars:
                seen.add(t)
            iters += 1
        if len(seen) >= count * 2 or iters >= MAX_ITERATIONS:
            break

    return _make_result(seen, "douyin", min_c, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# 统一调度入口
# ═══════════════════════════════════════════════════════════════════════════════

GENERATORS = {
    "shopee_th": _gen_shopee,
    "lazada_th": _gen_lazada,
    "tiktok_global": _gen_tiktok,
    "temu": _gen_temu,
    "amazon": _gen_amazon,
    "taobao": _gen_taobao,
    "pinduoduo": _gen_pdd,
    "douyin": _gen_douyin,
}


def dispatch(product_cn: str, plat_key: str, cat_data: dict,
             max_chars: int) -> list[dict]:
    """根据平台分发到对应的标题生成器"""
    gen = GENERATORS.get(plat_key)
    if gen:
        return gen(product_cn, cat_data, max_chars, TARGET_TITLE_COUNT)

    # 兜底：泰语 Shopee 风格
    return _gen_shopee(product_cn, cat_data, max_chars, TARGET_TITLE_COUNT)
