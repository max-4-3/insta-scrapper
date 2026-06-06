import sys, json
from typing import Callable, Generator

from httpx import Client
from pathlib import Path
from time import sleep
from random import random

from env import load_env

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "X-IG-App-ID": "936619743392459",
        "X-ASBD-ID": "359341",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Origin": "https://www.instagram.com",
        "Pragma": "no-cache",
}
COOKIES = load_env()

def download_file(client: Client, url: str, path: Path, callback: Callable[[int, int], None]) -> Path:
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".part")

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with client.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", -1))
            done = 0

            if (total > 0 and path.exists() and path.stat().st_size == total):
                if callback:
                    callback(total, total)
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
                return path

            with tmp_path.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    done += len(chunk)
                    if callback is not None:
                        callback(done, total)

        tmp_path.replace(path)
        return path

    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

def get_key(post: dict):
    width = post.get("width", 1)
    height = post.get("height", 1)
    return width * height

def get_url(media: dict) -> str | None:
    video_versions: list[dict] = media.get("video_versions") or []
    return max(video_versions, key=get_key, default={}).get("url")

def get_id(media: dict) -> str:
    return media.get("code") or media["id"]

def get_title(media: dict) -> str:
    user = media.get("user")
    if user:
        name = user.get("username") or user["id"]
        title = f"Highlight by {name} [{get_id(media)}]"
    else:
        title = get_id(media)

    return title

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
    data = (
        json.loads(resp.text) if "json" in resp.headers.get("Content-Type", "") else {}
    )

    if resp.status_code != 200 or data.get("status", "") != "ok" or not data.get("reels"):
        raise RuntimeError(
            f"[{resp.status_code}] unable to retrive media:\n{resp.text}"
        )

    for key, node in data["reels"].items():
        extensions: dict[str, dict] = {
            "user": node["user"],
            "highlight_cover": node["cover_media"],
        }

        items = sorted(
            ({**item, **extensions} for item in node.get("items") or []),
            key=lambda item: int(item.get("taken_at", 0)),
            reverse=True,
        )

        print("found items for", key, "items:", len(items), "results:", len(results))
        for item in items:
            results.append(item)
            yield item

    return results

def main():
    in_path = sys.argv[1]
    if in_path == "-":
        json_text = sys.stdin.read()
    else:
        json_text = Path(in_path).read_text()

    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True, parents=True)

    with (Client(base_url="https://www.instagram.com", follow_redirects=True, headers=HEADERS, cookies=COOKIES) as client,
          Client(follow_redirects=True, headers={"User-Agent": HEADERS["User-Agent"]}) as dl_client):
        highlights = list(filter(lambda media: media.get("__typename", "") == "XDTReelDict", json.loads(json_text)))
        stories_seen = 0

        for highlight in highlights:
            try:
                medias = get_media(client, highlight["id"])
                if not medias:
                    print("unabel to extract medias for highlight:", highlight["id"])
                    continue
            except Exception as e:
                print("extract error on highlight:", highlight["id"])
                continue

            counter = 1
            for idx, media in enumerate(medias):
                try:
                    url = get_url(media)
                    if not url:
                        print("unable to extract url for", get_id(media), "maybe an image?")
                        continue
                except Exception as e:
                    print("extract error on:", get_title(media), get_id(media))
                    continue

                try:
                    title = get_title(media)
                    path = output_dir / highlight["id"] / f"{title}.mp4"
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
