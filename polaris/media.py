import re
import pathlib
import json
import sys

from httpx import Client

from downloaders import DOWNLOADERS

def extract(data: str) -> dict:
    # 1. Locate where the JSON object begins
    pattern = re.compile(r'{"xig_polaris_media"\s*:\s*')
    srch = pattern.search(data)
    if not srch:
        return {}

    # 2. Extract starting from the matched '{'
    start_idx = srch.start()
    decoder = json.JSONDecoder()

    try:
        # raw_decode parses a valid JSON object starting at start_idx
        # and returns a tuple: (parsed_dict, end_index_position)
        obj, _ = decoder.raw_decode(data, idx=start_idx)
        return obj
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return {}

def main():
    if len(sys.argv) < 2:
        raise ValueError("post link in required!")

    link = sys.argv.pop()
    temp = pathlib.Path("./tmp/" if len(sys.argv) < 2 else sys.argv.pop())

    temp.mkdir(parents=True, exist_ok=True)

    with Client(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:155.0) Gecko/20100101 Firefox/155.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": link,
        "Sec-Fetch-Mode": "navigate",
    }) as client:

        is_file = False

        if not pathlib.Path(link).exists():
            page = client.get(link)
            page.raise_for_status()
            print(f"[{page.status_code}] GET {link} [{len(page.history)}]")

            path = (temp / (re.sub(r'[^A-Za-z0-9_]+', '-', link))).with_suffix(".page")
            text = page.read().decode(errors="ignore")

            path.write_text(text)
            is_file = not True

            print(f"[->{len(text)}] {path}")
        else:
            path = pathlib.Path(link)
            text = path.read_text()
            is_file = True

            print(f"[<-{len(text)}] {path}")

        data = extract(text)["xig_polaris_media"]
        polaris_media = data["if_not_gated_logged_out"]
        if not is_file or not path.with_suffix(".json").exists():
            path.with_suffix(".json").write_text(json.dumps(polaris_media, indent=2, ensure_ascii=False))
            print(f"[JSON: ->{len(polaris_media.keys())}] {path.with_suffix(".json")}")

        user = polaris_media["user"]
        media = polaris_media
        out = pathlib.Path("./out/") / str(user["username"]) / str("%s-%s" % (data["code"], data["pk"]))

        out.mkdir(exist_ok=True, parents=True)
        downloader = DOWNLOADERS.get(media["__typename"], None)
        if not downloader:
            print(f"[ERROR] Unable to find downloader for type '{media["__typename"]}'")
            return 1

        print(f"[DOWNLOADER] passing control to '{downloader.__name__}'")
        try:
            ok, path = downloader(media, user, out)
            (out / "init-data.json").write_text(json.dumps({"media": media, "user": user}, indent=2, ensure_ascii=False))

            if ok:
                print(f"[SAVED] '{link}' -> '{path.resolve()}'")
            else:
                print(f"[ERROR] unable to save '{link}'")
        except NotImplementedError:
            print(f"[WARN] NotImplemented for '{media["__typename"]}'")


if __name__ == "__main__":
    main()
