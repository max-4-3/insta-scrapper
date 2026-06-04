import sys, json
from typing import Callable

from httpx import Client
from pathlib import Path
from time import sleep
from random import random


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
        "X-Asbd-Id": "359341",
}

def get_key(post: dict):
    width = post.get("width", 1)
    height = post.get("height", 1)
    return width * height

def get_url(client: Client, post: dict) -> str | None:
    reel_id = post["pk"]
    path = f"/api/v1/media/{reel_id}/info/"
    resp = client.get(path, follow_redirects=True)
    resp.raise_for_status()
    post = resp.json()

    video_versions: list[dict] = [version for item in post["items"] for version in item.get("video_versions", [])]
    return max(video_versions, key=get_key, default={}).get("url")

def get_id(post: dict) -> str:
    return post.get("code") or post["id"]

def get_post_title(post: dict) -> str:
    return (user := post.get("user")) and f"Video by {user["id"]} [{get_id(post)}]" or get_id(post)

def show_prog(prefix: str, done: int, total: int) -> None:
    perc = (total > 0 and (done / total) or -1) * 100

    print("\r\033[2K" + prefix, done, total, f"{perc:.1f}%", end="")

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
def main():
    in_path = sys.argv[1]
    if in_path == "-":
        json_text = sys.stdin.read()
    else:
        json_text = Path(in_path).read_text()

    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True, parents=True)

    with Client(follow_redirects=True, headers=HEADERS) as client:
        posts = list(filter(lambda media: int(media.get("media_type", -1)) == 2, json.loads(json_text)))
        counter = 1

        for idx, (post, url) in enumerate(zip(posts, map(lambda p: get_url(client, p), posts))):
            if url is None:
                print("post has no video:", get_id(post))
                continue
            
            try:
                path = (output_dir / get_post_title(post)).with_suffix(".mp4")
                download_file(client, url, path, lambda done, total: show_prog(f"{counter:02}. {get_post_title(post)}", done, total))
                counter += 1
                print()
            except Exception as e:
                print("\n", "download error on:", get_id(post), "error:", e)
            finally:
                sleep((idx % (4 if idx % 10 == 0 else 2)) + random())


        print("total video posts:", len(posts))

if __name__ == "__main__":
    main()
