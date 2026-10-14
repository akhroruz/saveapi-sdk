"""Resolve a post link and save the first media file to disk.

    pip install saveapi
    SAVEAPI_KEY=sk_live_... python download.py "https://www.tiktok.com/@zachking/video/6768504823336815877"
"""

import sys

import httpx

from saveapi import SaveAPI, SaveAPIError


def main(url: str) -> None:
    with SaveAPI() as api:
        try:
            post = api.download(url)
        except SaveAPIError as error:
            sys.exit(f"{error.code}: {error.message}")

    media = post["medias"][0]
    name = f"{post['platform']}-{post.get('video_id') or 'media'}.{media['ext'] or 'bin'}"

    # The URL points at the platform's CDN: stream it, do not load it into memory.
    with httpx.stream("GET", media["url"], follow_redirects=True, timeout=120) as response:
        response.raise_for_status()
        with open(name, "wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)

    print(f"saved {name} ({post['credits']['spent']} credits spent, {post['credits']['remaining']} left)")


if __name__ == "__main__":
    main(sys.argv[1])
