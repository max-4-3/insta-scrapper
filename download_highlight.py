import sys, json
from typing import Generator

from httpx import Client
from pathlib import Path
from time import sleep
from random import random

from utils import Clients, dict_try, download_file, validate_json_response

def get_key(post: dict):
    width = post.get("width", 1)
    height = post.get("height", 1)
    return width * height

def get_max_url(items: list[dict]) -> str | None:
    return max(items, key=get_key, default={}).get("url")

def get_id(media: dict) -> str:
    return dict_try(media, "code", "id", allow_null=False)

def get_title(media: dict) -> str:
    user = media.get("user")
    if user:
        prefix = is_video(media) and 'Video' or 'Image'
        title = f"{prefix} Highlight by {dict_try(user, "username", "id")} [{get_id(media)}]"
    else:
        title = get_id(media)

    return title

def get_highlight_title(highlight: dict) -> str:
    return dict_try(highlight, "title", "id", allow_null=False)

def show_prog(prefix: str, done: int, total: int) -> None:
    perc = (total > 0 and (done / total) or -1) * 100

    print("\r\033[2K" + prefix, done, total, f"{perc:.1f}%", end="")

def get_media(client: Client, highlight_id: str) -> Generator[dict, None, list[dict]]:
    results = []
    params = {
        "reel_ids": highlight_id
    }
    path = "/api/v1/feed/reels_media/"

    resp = client.request("GET", path, params=params)
    reels = validate_json_response(resp, expected_key="reels")

    for key, node in reels.items():
        extensions: dict[str, dict] = {
            "user": node["user"],
            "highlight_cover": node["cover_media"],
        }

        items = sorted(
            ({**item, **extensions} for item in node.get("items") or []),
            key=lambda item: int(item.get("taken_at", 0)),
            reverse=True,
        )

        print("found items for", key, "items:", len(items))
        for item in items:
            results.append(item)
            yield item

    return results

def is_video(media: dict):
    return bool(media.get("video_versions"))

def main():
    in_path = sys.argv[1]
    if in_path == "-":
        json_text = sys.stdin.read()
    else:
        json_text = Path(in_path).read_text()

    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True, parents=True)

    with Clients.authed() as client, Clients.normal() as dl_client:
        highlights = list(filter(lambda media: bool(media.get("__typename", "")), json.loads(json_text)))
        stories_seen = 0

        for id, highlight in zip(map(lambda highlight: str(highlight["id"]), highlights), highlights):
            try:
                medias = get_media(client, id)
                if not medias:
                    print("unabel to extract medias for highlight:", id)
                    continue
            except Exception as e:
                print("extract error on highlight:", id)
                continue

            counter = 1
            root = output_dir / id
            print("saving", get_highlight_title(highlight), "highlight under:", root)

            for idx, media in enumerate(medias):
                try:
                    video = is_video(media)
                    if video:
                        url = get_max_url(media.get("video_versions") or [])
                    else:
                        url = get_max_url((media.get("image_versions2") or {}).get("candidates") or [])

                    if not url:
                        print("unable to extract url for:", get_id(media))
                        continue
                except Exception as e:
                    print("extract error on:", get_title(media), get_id(media))
                    continue

                try:
                    title = get_title(media)
                    suffix = video and '.mp4' or '.jpg'
                    path = root / f"{title}{suffix}"
                    download_file(dl_client, url, path, lambda done, total: show_prog(f"{counter:02}. {title}", done, total))
                    counter += 1
                    print()
                except Exception as e:
                    print("\n", "download error on:", get_id(media), "error:", e)
                finally:
                    sleep((idx % (2 if idx % 10 == 0 else 1)) + random())

            print("stories downloaded:", counter)
            stories_seen += counter

        print("total highlights:", len(highlights), "total stories:", stories_seen)

if __name__ == "__main__":
    main()
