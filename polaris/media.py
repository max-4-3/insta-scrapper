import pathlib

from polaris.utils import extract_json, retrive_content, save_json, get_client
from polaris.downloaders import DOWNLOADERS


def main(link: str, out_path: str) -> int:
    with get_client() as client:
        is_file = pathlib.Path(link).exists()
        text, path = retrive_content(link, client)

        data = extract_json(text, "xig_polaris_media")["xig_polaris_media"]
        if not (is_file and path.with_suffix(".json").exists()):
            save_json(data, path.with_suffix(".json"))

        polaris_media = data["if_not_gated_logged_out"]
        user = polaris_media["user"]
        media = dict(polaris_media)

        username, typ = str(user["username"]), str(media["__typename"])
        out = pathlib.Path(out_path).joinpath(username, data.get("code") or data["pk"])

        out.mkdir(exist_ok=True, parents=True)
        downloader = DOWNLOADERS.get(typ, None)
        if not downloader:
            print(f"[ERROR] Unable to find downloader for type '{typ}'")
            return 1

        print(f"[DOWNLOADER] passing control to '{downloader.__name__}'")
        ok = False
        try:
            ok, path = downloader(media, user, out)
            save_json({"media": media, "user": user}, (out / "init-data").with_suffix(".json"))

            if ok:
                print(f"[SAVED] '{link}' -> '{path.resolve()}'")
            else:
                print(f"[ERROR] unable to save '{link}'")
        except NotImplementedError:
            print(f"[WARN] NotImplemented for '{typ}'")

        return int(not ok)
