import sys, json
from typing import Iterable

from pathlib import Path
from time import sleep
from random import random

from utils import Clients, dict_try, download_file

def get_key(post: dict):
    width = post.get("width", 1)
    height = post.get("height", 1)
    return width * height

def get_url(post: dict) -> str | None:
    video_versions: list[dict] = post.get("video_versions") or []
    return max(video_versions, key=get_key, default={}).get("url")

def is_video(post: dict) -> bool:
    return bool( # filter video nodes with valid url
        post.get("__typename", "") == "XDTMediaDict"
        and post.get("video_versions")
    )

def get_id(post: dict) -> str:
    return dict_try(post, "code", "id")

def get_post_title(post: dict) -> str:
    return (user := post.get("user")) and f"Video by {dict_try(user, "username", "id")} [{get_id(post)}]" or get_id(post)

def show_prog(prefix: str, done: int, total: int) -> None:
    perc = (total > 0 and (done / total) or -1) * 100

    print("\r\033[2K" + prefix, done, total, f"{perc:.1f}%", end="")

def flattern(posts: Iterable[dict]) -> list[dict]:
    # carousel_media
    posts_ = []

    for post in posts:
        if post.get("__typename", "") == "XDTMediaDict" and (carousels := post.get("carousel_media", [])):
            for carousel in carousels:
                carousel["user"] = post["user"]
                carousel["like_count"] = post.get("like_count", -1)
                posts_.append(carousel)
        else:
            posts_.append(post)

    return posts_

def main():
    in_path = sys.argv[1]
    if in_path == "-":
        json_text = sys.stdin.read()
    else:
        json_text = Path(in_path).read_text()

    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True, parents=True)

    with Clients.normal() as client:
        posts = list(flattern(filter(is_video, json.loads(json_text))))
        counter = 1

        for idx, (post, url) in enumerate(zip(posts, map(get_url, posts))):
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
