import sys, json

from httpx import Client
from pathlib import Path
from time import sleep
from random import random

from utils import Clients, dict_try, download_file, validate_json_response

def get_key(post: dict):
    width = post.get("width", 1)
    height = post.get("height", 1)
    return width * height

def get_url(client: Client, post: dict) -> str | None:
    reel_id = post["pk"]
    path = f"/api/v1/media/{reel_id}/info/"

    resp = client.request("GET", path, follow_redirects=True)
    posts = validate_json_response(resp, expected_key="items")
    
    video_versions: list[dict] = [version for item in posts for version in item.get("video_versions") or []]
    return max(video_versions, key=get_key, default={}).get("url")

def get_id(post: dict) -> str:
    return dict_try(post, "code", "id")

def get_post_title(post: dict) -> str:
    return (user := post.get("user")) and f"Video by {dict_try(user, "username", "id")} [{get_id(post)}]" or get_id(post)

def show_prog(prefix: str, done: int, total: int) -> None:
    perc = (total > 0 and (done / total) or -1) * 100

    print("\r\033[2K" + prefix, done, total, f"{perc:.1f}%", end="")

def main():
    in_path = sys.argv[1]
    if in_path == "-":
        json_text = sys.stdin.read()
    else:
        json_text = Path(in_path).read_text()

    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True, parents=True)

    with Clients.normal() as client:
        posts = list(filter(lambda media: int(media.get("media_type", -1)) == 2, json.loads(json_text)))
        counter = 1

        for idx, post in enumerate(posts):
            try:
                url = get_url(client, post)
                if url is None:
                    print("post has no video:", get_id(post))
                    continue

                path = (output_dir / get_post_title(post)).with_suffix(".mp4")
                download_file(client, url, path, lambda done, total: show_prog(f"{counter:02}. {get_post_title(post)}", done, total))
                counter += 1
                print()
            except Exception as e:
                print("\n", "download error on:", get_id(post), "error:", e)
                raise
            finally:
                sleep((idx % (4 if idx % 10 == 0 else 2)) + random())


        print("total video posts:", len(posts))

if __name__ == "__main__":
    main()
