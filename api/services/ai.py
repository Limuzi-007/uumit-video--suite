"""AI-powered services (translation, summarization, etc.)"""
import os
import json
import httpx
from typing import Optional
from loguru import logger

# ─── Optional LLM Translation ─────────────────────────────────────────

def translate_text(text: str, source: str = "zh", target: str = "en") -> str:
    """
    Translate text using a configured LLM API.
    Falls back to simple char-based mapping if no API key.
    """
    api_key = os.getenv("LLM_API_KEY", "")
    api_url = os.getenv("LLM_API_URL", "")

    if api_key and api_url:
        return _translate_via_llm(text, source, target, api_key, api_url)
    else:
        return _translate_fallback(text, source, target)


def _translate_via_llm(text: str, source: str, target: str, api_key: str, api_url: str) -> str:
    """Translate using configured LLM."""
    prompt = f"Translate the following text from {source} to {target}. Return ONLY the translation, no explanations.\n\n{text}"

    try:
        resp = httpx.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"LLM translation failed: {e}, using fallback")
        return _translate_fallback(text, source, target)


def _translate_fallback(text: str, source: str, target: str) -> str:
    """
    Fallback: simple token-by-token marker.
    In production, use a proper translation library or service.
    """
    # Simple bilingual dictionary for demo
    dictionary = {
        "你好": "Hello",
        "谢谢": "Thank you",
        "视频": "Video",
        "剪辑": "Editing",
        "字幕": "Subtitle",
        "上传": "Upload",
        "下载": "Download",
        "成功": "Success",
        "失败": "Failed",
        "处理中": "Processing",
        "完成": "Completed",
    }

    if target == "en":
        for zh, en in dictionary.items():
            text = text.replace(zh, en)
        return text
    elif target == "zh":
        for zh, en in dictionary.items():
            text = text.replace(en, zh)
        return text
    return text


# ─── Segment-based translation ────────────────────────────────────────

def translate_segments(segments: list[dict], source: str, target: str) -> list[dict]:
    """Translate each segment's text."""
    translated = []
    for seg in segments:
        new_seg = dict(seg)
        new_seg["original_text"] = seg.get("text", "")
        new_seg["text"] = translate_text(seg.get("text", ""), source, target)
        translated.append(new_seg)
    return translated
