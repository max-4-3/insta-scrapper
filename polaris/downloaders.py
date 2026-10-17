import json
from typing import Callable
from datetime import datetime
from pathlib import Path


from httpx import Client
type DownloaderFn = Callable[[dict, dict, Path], tuple[bool, Path]]


def download_carousel_media(media: dict, user: dict, out: Path) -> tuple[bool, Path]:
    downloaded: list[tuple[dict, str]] = []

    for post in media["carousel_media"]:
        typ = post["__typename"]
        if typ not in DOWNLOADERS:
            print("[WARN] no downloader found for '%s'" % typ)
            continue

        try:
            ok, file = DOWNLOADERS[typ](post, user, out)
            if ok:
                print(f"[SAVED] '{file}'")
                downloaded.append((post, str(file.resolve().absolute())))
            else:
                print(f"[ERROR] unable to save '{post["pk"]}'")
        except NotImplementedError:
            print(f"[WARN] NotImplemented for '{typ}'")

    print(f"[FINISHED] Downloaded '{len(downloaded)}' medias in '{out.resolve()}'")
    (out / f"{user["username"]}-{datetime.now().timestamp()}-download-info.json").write_text(json.dumps(downloaded, indent=2))

    return (True, out)


def download_video_media(media: dict, user: dict, out: Path) -> tuple[bool, Path]:
    name = "{username}-{pid}".format_map({
        "username": user["username"],
        "pid": media["pk"],
    })

    path = out / name
    path.parent.mkdir(exist_ok=True, parents=True)

    with Client(follow_redirects=True) as client:
        thumb_link = media["image_versions2"]["candidates"][0]["url"]
        with client.stream("GET", thumb_link) as stream, path.with_suffix(".thumb.jpg").open('wb') as file:
            file.write(stream.read())
            print(f"[THUMB] Saved '{path.with_suffix(".thumb.jpg")}'")

        video_link = media["video_versions"][0]["url"]
        with client.stream("GET", video_link) as stream, path.with_suffix(".mp4").open('wb') as file:
            file.write(stream.read())
            print(f"[VIDEO] Saved '{path.with_suffix(".mp4")}'")

    return True, path


def download_image_media(media: dict, user: dict, out: Path) -> tuple[bool, Path]:
    name = "{username}-{pid}.jpg".format_map({
        "username": user["username"],
        "pid": media["pk"],
    })
    link = media["image_versions2"]["candidates"][0]["url"]

    out.mkdir(exist_ok=True, parents=True)

    with Client() as client, client.stream("GET", link, follow_redirects=True) as steam, (out / name).open('wb') as file:
        file.write(steam.read())
        print(f"[IMAGE] Saved '{name}'")

    return True, out / name


DOWNLOADERS: dict[str, DownloaderFn] = {
    "XIGPolarisCarouselMedia": download_carousel_media,
    "XIGPolarisVideoMedia": download_video_media,
    "XIGPolarisImageMedia": download_image_media,
}
