# -*- coding: utf-8 -*-
"""词库管理模块 — 加载、保存、备份、注入热词（支持新旧两套词库）"""

import json
import logging
from datetime import datetime
from pathlib import Path

from config import DATA_DIR

logger = logging.getLogger(__name__)

# ── 硬编码兜底全类目词库（旧版 5 类目） ──
BUILTIN_LEXICON = {
    "_meta": {"version": "2.1", "description": "内置全类目词库", "last_updated": "2026-05-26"},
    "platform_limits": {
        "shopee_th":     {"max_chars": 120, "name_cn": "Shopee泰国站"},
        "lazada_th":     {"max_chars": 130, "name_cn": "Lazada泰国站"},
        "tiktok_global": {"max_chars": 100, "name_cn": "TikTok海外"},
        "temu":          {"max_chars": 150, "name_cn": "Temu"},
        "amazon":        {"max_chars": 200, "name_cn": "Amazon"},
        "taobao":        {"max_chars": 60,  "name_cn": "淘宝"},
        "pinduoduo":     {"max_chars": 120, "name_cn": "拼多多"},
        "douyin":        {"max_chars": 55,  "name_cn": "抖音"},
    },
    "categories": {
        "electronics": {
            "display_name": "数码3C/家电",
            "subcategories": ["智能手表","蓝牙耳机","手机壳","充电宝","音箱","机械键盘","鼠标","摄像头","麦克风","数据线"],
            "base": ["สมาร์ทวอทช์","หูฟังบลูทูธ","เคสมือถือ","พาวเวอร์แบงค์","ลำโพงบลูทูธ","คีย์บอร์ด","เมาส์","กล้องเว็บแคม","สายชาร์จ","ไมโครโฟน"],
            "material_specs": ["กันน้ำ IP68","Bluetooth 5.3","แบตอึด 5000mAh","ไร้สาย TWS","4K Ultra HD","PD 65W Fast Charge","ANC ตัดเสียงรบกวน","RGB 16 ล้านสี","USB-C","MagSafe"],
            "scene_audience": ["เล่นเกม","ฟังเพลง","ออกกำลังกาย","ทำงาน Office","เรียนออนไลน์","ถ่าย Vlog","ไลฟ์สด TikTok","วิ่งมาราธอน","ขับรถ","ฟิตเนส"],
            "longtail": ["ขายดีอันดับ 1","ราคาถูกคุ้มค่า","คุณภาพเสียงดีเยี่ยม","ทนทานใช้งานนาน","น้ำหนักเบาพกพา","พกพาสะดวก","เสียงชัดใส","ลดราคาพิเศษ","ของแท้ 100%","พร้อมส่งด่วน"]
        },
        "fashion_beauty": {
            "display_name": "美妆个护/服装鞋包",
            "subcategories": ["面霜","防晒霜","套装","包包","鞋子","裙子","T恤","护肤品","口红","香水"],
            "base": ["ครีมบำรุงผิว","กันแดด","ชุดเซ็ตแฟชั่น","กระเป๋าแฟชั่น","รองเท้า","ชุดเดรส","เสื้อยืด","เซรั่มบำรุง","ลิปสติก","น้ำหอม"],
            "material_specs": ["SPF50+ PA++++","คอลลาเจน","วิตามินซี","Aloe Vera","เซราไมด์","กรดไฮยาลูรอนิก","Retinol","Niacinamide","SPF30 PA+++","Alcohol-free"],
            "scene_audience": ["ผิวขาวใส","ลดรอยสิว","กันแดดทุกวัน","แต่งหน้าทำงาน","ออกงานกลางคืน","ลุค Everyday","ลุค Casual","สาวออฟฟิศ","หนุ่มเกาหลี","วัยรุ่น"],
            "longtail": ["ขายดีที่สุด","ราคาถูกสุดคุ้ม","คุณภาพดีมาก","ของแท้แบรนด์ดัง","มาใหม่ล่าสุด","ยอดนิยม 2026","พร้อมส่งฟรี","ลดราคา 50%","สาวไทยแนะนำ","ผิวแพ้ง่ายใช้ได้"]
        },
        "mother_baby": {
            "display_name": "母婴玩具",
            "subcategories": ["婴儿推车","餐椅","纸尿裤","奶瓶","婴儿衣服","玩具","背带","爬行垫","学步车","安抚玩具"],
            "base": ["รถเข็นเด็ก","เก้าอี้ทานข้าวเด็ก","ผ้าอ้อมสำเร็จรูป","ขวดนมเด็ก","ชุดเด็กอ่อน","ของเล่นเด็ก","เป้อุ้มเด็ก","เบาะรองคลาน","รถหัดเดิน","ตุ๊กตาเด็ก"],
            "material_specs": ["BPA-free Food Grade","ผ้า Organic Cotton","ผ้าฝ้าย 100%","Silicone ทางการแพทย์","PP Food Grade","ผ้ามัสลิน","ABS ปลอดสารพิษ","ยางพาราธรรมชาติ","Non-toxic","กันน้ำ"],
            "scene_audience": ["เด็กแรกเกิด","ทารก 0-6 เดือน","วัยหัดเดิน","กิจกรรมกลางแจ้ง","ให้นมลูก","นอนหลับ","เล่นสนุก","อาบน้ำ","ทานข้าว","คุณแม่มือใหม่"],
            "longtail": ["ขายดีอันดับ 1","ราคาถูกปลอดภัย","คุณภาพดีเยี่ยม","ปลอดภัยสำหรับเด็ก","ผ่านมาตรฐาน อย.","พร้อมส่งด่วน","คุณแม่แนะนำ","ลดราคาพิเศษ","เสริมพัฒนาการ","ทนทานใช้งานได้นาน"]
        },
        "home_outdoor": {
            "display_name": "居家生活/户外露营",
            "subcategories": ["月亮椅","折叠桌","蛋卷桌","帐篷","收纳架","藤编家具","户外桌椅套装","折叠躺椅","吊床","收纳箱"],
            "base": ["เก้าอี้พระจันทร์","โต๊ะพับ","โต๊ะไม้พับ","เต็นท์แคมป์ปิ้ง","ชั้นวางของ","เฟอร์นิเจอร์หวายเทียม","ชุดโต๊ะเก้าอี้สนาม","เก้าอี้นอนพับ","เปลญวน","กล่องเก็บของ"],
            "material_specs": ["อลูมิเนียม","ผ้า Oxford 600D","หวายเทียม PE","ไม้สนแท้","ไม้ไผ่","โพลีเอสเตอร์","ผ้า Canvas","สแตนเลส 304","พลาสติก PP","ผ้า Ripstop"],
            "scene_audience": ["แคมป์ปิ้ง","ปิกนิก","ชายหาด","สนามหญ้า","ระเบียงคอนโด","สวนหลังบ้าน","ลานกางเต็นท์","ร้านกาแฟ","รีสอร์ท","ออฟฟิศ"],
            "longtail": ["ขายดีอันดับ 1","ราคาถูกคุ้มค่า","คุณภาพดีเยี่ยม","ทนทานใช้งานกลางแจ้ง","น้ำหนักเบาพกพา","พับเก็บง่าย","ติดตั้งเร็ว","พร้อมส่งด่วน","ลดราคาพิเศษ","Outdoor ขายดี"]
        },
        "food_beverage": {
            "display_name": "食品饮料",
            "subcategories": ["零食","茶叶","咖啡","保健品","方便面","调味料","坚果","果汁","奶粉","蜂蜜"],
            "base": ["ขนมขบเคี้ยว","ชาไทย","กาแฟสำเร็จรูป","อาหารเสริม","บะหมี่กึ่งสำเร็จรูป","เครื่องปรุงรส","ถั่วอบแห้ง","น้ำผลไม้","นมผง","น้ำผึ้งแท้"],
            "material_specs": ["ออร์แกนิค 100%","น้ำตาล 0%","Gluten-free","Non-GMO","โปรตีนสูง","ไฟเบอร์สูง","วิตามินรวม","คอลลาเจนเปปไทด์","สารสกัดจากธรรมชาติ","HACCP รับรอง"],
            "scene_audience": ["ลดน้ำหนัก","ดูแลสุขภาพ","บำรุงสมอง","เสริมภูมิคุ้มกัน","ออกกำลังกาย","ผู้สูงอายุ","เด็กนักเรียน","สาวออฟฟิศ","หนุ่มฟิตเนส","ทุกเพศทุกวัย"],
            "longtail": ["ขายดีอันดับ 1","ราคาถูกคุ้มค่า","อร่อยถูกใจ","ปลอดภัย อย. รับรอง","ส่งฟรีทั่วไทย","ลดราคาพิเศษ","พร้อมส่งทันที","ของดีประจำปี","ยอดขายสูงสุด","คุณภาพระดับพรีเมียม"]
        },
    },
}


def load_lexicon(lexicon_path: Path) -> dict:
    """
    加载词库。优先读文件，失败则用内置兜底。
    新版：尝试加载 data/category_system.json（40 类目），合并到结果中。
    返回值永远是有效字典，绝不会返回空。
    """
    result = None

    # 1. 尝试加载旧版词库（平台限制 + 元数据）
    try:
        if lexicon_path.exists():
            with open(lexicon_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("categories") and data.get("platform_limits"):
                result = data
                logger.info("旧版词库从文件加载成功: %s", lexicon_path)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("旧版词库文件读取失败: %s", e)

    if result is None:
        result = BUILTIN_LEXICON.copy()

    # 2. 尝试加载新版 40 类目系统
    cat_system_path = DATA_DIR / "category_system.json"
    if not cat_system_path.exists():
        # 兼容旧位置
        alt = lexicon_path.parent / "category_system.json"
        if alt.exists():
            cat_system_path = alt

    try:
        if cat_system_path.exists():
            with open(cat_system_path, "r", encoding="utf-8") as f:
                new_cats = json.load(f)
            if new_cats and len(new_cats) > 5:
                result["categories"] = new_cats
                result.setdefault("_meta", {})["category_system"] = True
                result["_meta"]["total_categories"] = len(new_cats)
                logger.info("新版 40 类目系统加载成功: %d 个类目", len(new_cats))
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("新版类目系统加载失败，使用旧版: %s", e)

    return result


def save_lexicon(lexicon_path: Path, data: dict) -> bool:
    """保存词库到文件"""
    try:
        lexicon_path.parent.mkdir(parents=True, exist_ok=True)
        data.setdefault("_meta", {})["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(lexicon_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except (IOError, OSError) as e:
        logger.error("词库保存失败: %s", e)
        return False


def backup_lexicon(backup_dir: Path, data: dict) -> bool:
    """创建词库备份"""
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(backup_dir / f"backup_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error("词库备份失败: %s", e)
        return False


def inject_keywords(cat_key: str, keywords: list[str], lexicon: dict) -> tuple[int, str]:
    """将热词注入指定类目的长尾词库（兼容新旧字段名）"""
    try:
        if cat_key not in lexicon.get("categories", {}):
            return 0, "类目不存在"
        cat = lexicon["categories"][cat_key]

        # 兼容：新版用 longtail_keywords，旧版用 longtail
        field = "longtail_keywords" if "longtail_keywords" in cat else "longtail"
        existing = set(cat.get(field, []))
        added = 0
        for kw in keywords:
            kw = kw.strip()
            if kw and kw not in existing:
                existing.add(kw)
                added += 1
        cat[field] = list(existing)
        return added, f"新增 {added} 条，当前共 {len(existing)} 条长尾词"
    except Exception as e:
        return 0, f"注入异常: {e}"
