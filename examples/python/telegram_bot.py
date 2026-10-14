"""A minimal Telegram downloader bot: send it a link, get the video back.

    pip install saveapi aiogram
    BOT_TOKEN=... SAVEAPI_KEY=sk_live_... python telegram_bot.py

Full walkthrough: https://saveapi.org/en/guides/telegram-bot/
"""

import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

from saveapi import AsyncSaveAPI, SaveAPIError

bot = Bot(os.environ["BOT_TOKEN"])
dp = Dispatcher()
api = AsyncSaveAPI()

FINAL = {
    "PRIVATE_CONTENT": "This post is private.",
    "MEDIA_NOT_FOUND": "This post was deleted or never existed.",
    "UNSUPPORTED_PLATFORM": "This site is not supported.",
    "INVALID_URL": "That does not look like a post link.",
}


@dp.message(F.text.startswith("http"))
async def on_link(message: Message) -> None:
    try:
        post = await api.download(message.text.strip())
    except SaveAPIError as error:
        await message.answer(FINAL.get(error.code, "Could not download this one, try again later."))
        return

    media = post["medias"][0]
    caption = (post["meta"].get("title") or "")[:1000]
    # Telegram fetches the file by URL itself: up to 5 MB for photos and 20 MB for
    # other files. Larger videos must be downloaded and uploaded as a file.
    if media["type"] == "video":
        await message.answer_video(media["url"], caption=caption)
    elif media["type"] == "image":
        await message.answer_photo(media["url"], caption=caption)
    else:
        await message.answer_audio(media["url"], caption=caption)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
