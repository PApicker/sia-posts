"""
Запускается GitHub Actions раз в 30 минут.
Читает posts/scheduled_posts.json, находит посты у которых scheduled_at <= now,
шлёт их в Telegram через бота, помечает как sent, удаляет картинки.
В конце workflow коммитит изменённые posts/.
"""

import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests


QUEUE_PATH = Path("posts/scheduled_posts.json")
IMAGES_DIR = Path("posts/images")

TG_TOKEN       = os.environ.get("TG_TOKEN", "")
_TG_CHAT_RAW   = os.environ.get("TG_CHAT_ID", "").strip()


def _normalize_chat_id(raw: str) -> str:
    """Если ввели голое число типа '3514119197' (Telegram показывает такой
    в инфо канала), добавляем префикс '-100'. Bot API не принимает голые ID."""
    if raw.startswith("@") or raw.startswith("-"):
        return raw
    if raw.isdigit() and len(raw) >= 9:
        return f"-100{raw}"
    return raw


TG_CHAT_ID = _normalize_chat_id(_TG_CHAT_RAW)


def fail(msg: str):
    print(f"::error::{msg}")
    sys.exit(1)


def tg_send_text(text: str) -> bool:
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={
            "chat_id": TG_CHAT_ID, "text": text,
            "disable_web_page_preview": True,
            "parse_mode": "Markdown",
        },
        timeout=30,
    )
    if not r.ok:
        print(f"sendMessage error: {r.status_code} {r.text[:200]}")
    return r.ok


def tg_send_photo(text: str, image_path: Path) -> bool:
    if not image_path.exists():
        print(f"image not found: {image_path}")
        return tg_send_text(text)
    # caption лимит 1024
    caption = text[:1020]
    with open(image_path, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
            data={"chat_id": TG_CHAT_ID, "caption": caption,
                  "parse_mode": "Markdown"},
            files={"photo": f}, timeout=60,
        )
    if not r.ok:
        print(f"sendPhoto error: {r.status_code} {r.text[:200]}")
    return r.ok


def main():
    if not TG_TOKEN or not TG_CHAT_ID:
        fail("TG_TOKEN / TG_CHAT_ID не заданы в secrets")
    if not QUEUE_PATH.exists():
        print("Очередь пуста (нет файла) — выходим")
        return
    try:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8") or "[]")
    except Exception as e:
        fail(f"Не могу прочитать очередь: {e}")
    if not isinstance(queue, list):
        fail("Очередь — не список")

    now = datetime.now(timezone.utc)
    posted = 0
    errors = 0
    for entry in queue:
        if entry.get("status") != "pending":
            continue
        scheduled = entry.get("scheduled_at", "")
        try:
            when = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            print(f"Skip {entry.get('id')}: bad scheduled_at {scheduled!r}")
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when > now:
            # Ещё рано
            continue

        text  = entry.get("text", "").strip()
        image = entry.get("image", "")
        if not text:
            entry["status"] = "skipped_empty"
            continue

        print(f"Posting {entry.get('id')}: scheduled {scheduled}")
        ok = False
        if image:
            ok = tg_send_photo(text, Path(image))
        else:
            ok = tg_send_text(text)

        if ok:
            entry["status"] = "sent"
            entry["sent_at"] = now.isoformat()
            posted += 1
            # Удаляем картинку чтобы репо не разрастался
            if image:
                img = Path(image)
                if img.exists():
                    try: img.unlink()
                    except OSError as e: print(f"can't delete {img}: {e}")
        else:
            entry["status"] = "error"
            entry["error_at"] = now.isoformat()
            errors += 1

    # Записываем обновлённую очередь
    QUEUE_PATH.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Done: posted={posted}, errors={errors}")


if __name__ == "__main__":
    main()
