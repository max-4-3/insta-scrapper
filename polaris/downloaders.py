from typing import Callable
from datetime import datetime
from pathlib import Path

from httpx import Client

from polaris.utils import save_json

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

    now = datetime.now().timestamp()
    username = user["username"]

    save_json({"downloaded": downloaded}, out.joinpath(f"{username}-{now}-downloaded-info").with_suffix(".json"))
    return (True, out)


def download_video_media(media: dict, user: dict, out: Path) -> tuple[bool, Path]:
    name = "{username}-{pid}".format_map({
        "username": user["username"],
        "pid": media["pk"],
    })

    path = out.joinpath(name)
    path.parent.mkdir(exist_ok=True, parents=True)

    with _download_client() as client:
        thumb_link = media["image_versions2"]["candidates"][0]["url"]
        _save(thumb_link, path, ".thumb.jpg", "THUMB", client)

        video_link = media["video_versions"][0]["url"]
        _save(video_link, path, ".mp4", "VIDEO", client)

    return (True, path)


def download_image_media(media: dict, user: dict, out: Path) -> tuple[bool, Path]:
    name = "{username}-{pid}".format_map({
        "username": user["username"],
        "pid": media["pk"],
    })

    path = out.joinpath(name)
    path.parent.mkdir(exist_ok=True, parents=True)

    with _download_client() as client:
        image_link = media["image_versions2"]["candidates"][0]["url"]
        _save(image_link, path, ".jpg", "IMAGE", client)

    return (True, path)


def _save(link: str, path: Path, suffix: str, typ: str, client: Client):
    p = path.with_suffix(suffix)
    with client.stream("GET", link) as stream, p.open('wb') as file:
        file.write(stream.read())

    print(f"[{typ.upper()}] Saved '{p}'")


def _download_client() -> Client:
    return Client(follow_redirects=True)


DOWNLOADERS: dict[str, DownloaderFn] = {
    "XIGPolarisCarouselMedia": download_carousel_media,
    "XIGPolarisVideoMedia": download_video_media,
    "XIGPolarisImageMedia": download_image_media,
}

__all__ = ("DOWNLOADERS",)
