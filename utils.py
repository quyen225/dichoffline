# utils.py
import os
import json
import time
import random
import logging
import re
from typing import Any, List, Dict

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

AUTOSAVE_DIR = os.path.join(os.path.dirname(__file__), "autosaves")
os.makedirs(AUTOSAVE_DIR, exist_ok=True)

def _autosave_path(filename: str) -> str:
    safe = filename or "untitled"
    safe = "".join(c for c in safe if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()
    return os.path.join(AUTOSAVE_DIR, f".autosave_{safe}.json")

def save_autosave(filename: str, data: List[str]) -> None:
    """
    Lưu tạm danh sách dòng đã dịch vào file JSON.
    Chữ ký: save_autosave(filename, data)
    """
    path = _autosave_path(filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": int(time.time()),
                "filename": filename,
                "data": data
            }, f, ensure_ascii=False, indent=2)
        logger.debug("Autosave saved: %s", path)
    except Exception as e:
        logger.exception("Lỗi khi lưu autosave: %s", e)
        raise

def load_autosave(filename: str) -> List[str] | None:
    """
    Load autosave nếu tồn tại và trả về danh sách dòng (hoặc None).
    """
    path = _autosave_path(filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            return payload.get("data")
    except Exception as e:
        logger.exception("Lỗi khi load autosave: %s", e)
        return None

def postprocess_translation(text: str, name_map: Dict[str, str]) -> str:
    """
    Phục hồi tên/placeholder trong kết quả dịch.
    Giả định name_map có dạng {original_name: replacement}.
    Hàm sẽ thay replacement trở lại original nếu replacement xuất hiện trong text.
    """
    if not text or not name_map:
        return text

    # Tạo map replacement -> original
    reverse_map = {}
    for orig, rep in name_map.items():
        if not rep:
            continue
        reverse_map.setdefault(rep, orig)

    # Thay thế các rep dài trước (giảm khả năng partial match)
    for rep in sorted(reverse_map.keys(), key=lambda x: -len(x)):
        orig = reverse_map[rep]
        try:
            text = text.replace(rep, orig)
        except Exception:
            continue
    return text

def count_hanzi(text: str) -> int:
    """
    Đếm số ký tự Hán (CJK Unified Ideographs) trong chuỗi.
    """
    if not text:
        return 0
    return sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')

def replace_names(text: str, name_map: Dict[str, str]) -> str:
    """
    Ví dụ đơn giản: thay các tên gốc bằng placeholder hoặc bản dịch tạm.
    Nếu bạn đã có replace_names khác, giữ nguyên; đây là fallback.
    """
    if not text or not name_map:
        return text
    out = text
    for orig, rep in name_map.items():
        if not rep:
            continue
        out = out.replace(orig, rep)
    return out

def is_chapter_title(line: str) -> bool:
    """
    Kiểm tra nhanh xem dòng có phải tiêu đề chương hay không (heuristic).
    """
    if not line: return False
    # Ví dụ: nếu dòng ngắn và chứa chữ số La Mã hoặc "Chương"
    if len(line) < 80 and ("Chương" in line or " chương " in line or line.strip().lower().startswith("chapter")):
        return True
    return False

def call_with_retry(func, *args, retries: int = 3, initial_backoff: float = 1.0,
                    max_backoff: float = 10.0, exceptions=(Exception,), jitter: bool = True, **kwargs):
    """
    Gọi func(*args, **kwargs) với retry + exponential backoff + jitter.
    """
    attempt = 0
    backoff = initial_backoff
    last_exc = None
    while attempt <= retries:
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exc = e
            attempt += 1
            if attempt > retries:
                break
            sleep_time = backoff
            if jitter:
                sleep_time = backoff * (0.5 + random.random() * 0.5)
            sleep_time = min(sleep_time, max_backoff)
            logger.warning("Call failed (attempt %d/%d): %s. Retrying in %.2fs", attempt, retries, e, sleep_time)
            time.sleep(sleep_time)
            backoff = min(backoff * 2, max_backoff)
    logger.exception("Gọi hàm thất bại sau %d lần: %s", retries, last_exc)
    raise last_exc

def remove_duplicate_words(text: str) -> str:
    """
    Tự động tìm và loại bỏ các từ hoặc cụm từ bị lặp lại liên tiếp.
    Ví dụ: "hắn hắn nói nói" -> "hắn nói"
           "chạy nhanh chạy nhanh" -> "chạy nhanh"
    """
    if not text:
        return ""
        
    # 1. Loại bỏ từ đơn lặp lại liên tiếp (ví dụ: hắn hắn, nàng nàng)
    # \b(\w+)\b: Tìm một từ nguyên vẹn
    # (\s+\1)+: Tìm một hoặc nhiều từ giống hệt phía sau, cách nhau bằng khoảng trắng
    text = re.sub(r'\b(\w+)\b(\s+\1)+', r'\1', text, flags=re.IGNORECASE)
    
    # 2. Loại bỏ cụm từ ngắn (2-4 từ) lặp lại liên tiếp (ví dụ: chạy nhanh chạy nhanh)
    # (.+?): Nhóm ký tự bất kỳ
    # \s+\1: Lặp lại nhóm ký tự đó phía sau
    # Áp dụng cho các cụm từ có độ dài từ 3 đến 20 ký tự để tránh bắt nhầm cấu trúc ngữ pháp
    for _ in range(2): # Chạy 2 vòng để quét sạch các cụm lặp lồng nhau
        text = re.sub(r'\b(.{3,20?})\b(\s+\1)+', r'\1', text, flags=re.IGNORECASE)
        
    return text.strip()
