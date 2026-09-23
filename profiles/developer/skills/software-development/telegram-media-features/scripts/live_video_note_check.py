"""Живая проверка: собрать video note из реальных видео и отправить в Telegram.

Зачем: юнит-тесты не доказывают, что Telegram примет файл. Приёмка медиа-фичи —
реальная отправка с полученным `message_id`.

Что делает: генерирует два исходника через ffmpeg (16:9 со звуком и 9:16 без),
приводит каждый к квадрату 640x640 (центр-кроп, звук сохраняется) и отправляет
владельцу как `video_note`. Печатает размеры, наличие звука и message_id.
Токен берётся из окружения и никогда не выводится.

Запуск одной строкой (составные команды режет гвард подтверждения):

    TELEGRAM_BOT_TOKEN=... ./.venv/bin/python \
        <skill_dir>/scripts/live_video_note_check.py --owner <chat_id>

Если у проекта есть свой сервис конвертации — заменить блок `convert()` на вызов
сервиса и читать путь результата из каталога вывода, а не из полей dataclass'а:
скрипт не должен зависеть от внутренних имён.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

FFMPEG = os.environ.get("FFMPEG_BIN", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE_BIN", "ffprobe")
SIZE = 640
CASES = (
    # имя, ширина входа, высота входа, есть ли звук
    ("16:9 со звуком", 1280, 720, True),
    ("9:16 без звука", 720, 1280, False),
)


def make_source(path: Path, width: int, height: int, with_audio: bool, seconds: int = 3) -> None:
    """Сгенерировать исходное видео через lavfi (без сети)."""
    command = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"testsrc=size={width}x{height}:rate=30:duration={seconds}",
    ]
    if with_audio:
        command += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-shortest"]
    command += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    command += ["-c:a", "aac"] if with_audio else ["-an"]
    command.append(str(path))
    subprocess.run(command, check=True, capture_output=True)


def probe(path: Path) -> dict[str, object]:
    """Размеры видео и наличие аудиодорожки через ffprobe."""
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json", "-show_streams", str(path)],
        check=True, capture_output=True, text=True,
    )
    streams = json.loads(result.stdout or "{}").get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {
        "width": int(video.get("width", 0)),
        "height": int(video.get("height", 0)),
        "audio": None if audio is None else audio.get("codec_name", "audio"),
    }


def convert(source: Path, output_dir: Path) -> Path:
    """Центр-кроп в квадрат, звук сохраняется; `-an` только если дорожки нет."""
    has_audio = probe(source)["audio"] is not None
    output = output_dir / f"note-{source.stem}.mp4"
    command = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-vf", f"crop='min(iw,ih)':'min(iw,ih)',scale={SIZE}:{SIZE}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-t", "60",
    ]
    command += ["-c:a", "aac", "-b:a", "96k"] if has_audio else ["-an"]
    command.append(str(output))
    subprocess.run(command, check=True, capture_output=True)
    return output


async def main() -> None:
    """Прогнать случаи и отправить кругляшки владельцу."""
    parser = argparse.ArgumentParser(description="Живая проверка video note")
    parser.add_argument("--owner", type=int, required=True, help="chat_id получателя")
    parser.add_argument("--token-env", default="TELEGRAM_BOT_TOKEN", help="имя переменной с токеном")
    args = parser.parse_args()

    token = os.environ.get(args.token_env, "").strip()
    if not token:
        print(f"нет {args.token_env} в окружении — живая проверка невозможна")
        return
    for binary in (FFMPEG, FFPROBE):
        if shutil.which(binary) is None and not Path(binary).is_file():
            print(f"нет {binary} — живая проверка невозможна")
            return

    from aiogram import Bot
    from aiogram.types import FSInputFile

    bot = Bot(token=token)
    with tempfile.TemporaryDirectory(prefix="live-video-note-") as tmp:
        workspace = Path(tmp)
        for name, width, height, with_audio in CASES:
            source = workspace / "source.mp4"
            make_source(source, width, height, with_audio)
            output_dir = workspace / "out"
            output_dir.mkdir(exist_ok=True)
            result = convert(source, output_dir)
            info = probe(result)
            print(
                f"{name}: {info['width']}x{info['height']}, звук={info['audio'] or 'нет'}, "
                f"{result.stat().st_size} байт"
            )
            if info["width"] != info["height"]:
                print(f"{name}: результат не квадрат — Telegram отклонит как video_note")
                continue
            sent = await bot.send_video_note(chat_id=args.owner, video_note=FSInputFile(result))
            print(f"отправлено как video_note: message_id={sent.message_id}")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
