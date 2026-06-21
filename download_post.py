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

def get_max_url(items: list[dict]) -> str | None:
    return max(items, key=get_key, default={}).get("url")

def is_video(post: dict) -> bool:
    return bool( # filter video nodes with valid url
        post.get("__typename", "") == "XDTMediaDict"
        and post.get("video_versions")
    )

def is_image(post: dict) -> bool:
    return bool( # filter video nodes with valid url
        post.get("__typename", "") == "XDTMediaDict"
        and post.get("image_versions2")
    )

def get_id(post: dict) -> str:
    return dict_try(post, "code", "id", allow_null=False)

def get_post_title(post: dict) -> str:
    prefix = is_video(post) and 'Video' or 'Image'
    return (user := post.get("user")) and f"{prefix} by {dict_try(user, "username", "id")} [{get_id(post)}]" or get_id(post)

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
        posts = list(flattern(filter(lambda post: is_video(post) or is_image(post), json.loads(json_text))))
        counter = 1

        for idx, (post, video) in enumerate(zip(posts, map(is_video, posts))):
            if video:
                url = get_max_url(post.get("video_versions") or [])
            else:
                url = get_max_url((post.get("image_versions2") or {}).get("candidates") or [])

            if url is None:
                print("invalid post:", get_id(post))
                continue
            
            try:
                suffix = ".mp4" if video else ".jpg"
                path = (output_dir / f"{get_post_title(post)}{suffix}")
                download_file(client, url, path, lambda done, total: show_prog(f"{counter:02}. {get_post_title(post)}", done, total))
                counter += 1
                print()
            except Exception as e:
                print("\n", "download error on:", get_id(post), "error:", e)
            finally:
                sleep((idx % (4 if idx % 10 == 0 else 2)) + random())


        print("total posts:", len(posts))

if __name__ == "__main__":
    main()
