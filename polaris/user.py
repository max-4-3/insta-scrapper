import re
import pathlib
import json
import sys

from httpx import Client

def extract(data: str, prefix: str) -> dict:
    # 1. Locate where the JSON object begins
    pattern = re.compile(
        rf'{prefix}.*?'
        r'(\{"xig_user_by_username"\s*:\s*)'
        if prefix else
        r'(\{"xig_user_by_username"\s*:\s*)'
        # r'(\{"xig_user_by_username"\s*:\s*)'
    )
    srch = pattern.search(data)
    if not srch:
        return {}

    # 2. Extract starting from the matched '{'
    start_idx = srch.start(1)
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
        raise ValueError("page link in required!")

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

        user = extract(text, 'adp_PolarisLoggedOutDesktopWWWProfileRootContentQueryRelayPreloader')["xig_user_by_username"]
        data = extract(text, 'adp_PolarisLoggedOutDesktopWWWProfile(?:Reels|Posts)TabContentQueryRelayPreloader')["xig_user_by_username"]
        is_posts = bool("polaris_ordered_timeline_connection" in data)

        if not is_file or not path.with_suffix(".json").exists():
            path.with_suffix(".json").write_text(json.dumps({"user": user, "data": data}, indent=2, ensure_ascii=False))
            print(f"[JSON: ->{len(user.keys())},{len(data.keys())}] {path.with_suffix(".json")}")

        links = []
        nodes = data["polaris_clips_connection" if not is_posts else "polaris_ordered_timeline_connection"]["edges"]
        for node in map(lambda conn: conn["node"], nodes):
            code, username, kind = node["code"], user["username"], "p" if is_posts else "reel"

            links.append(f"https://www.instagram.com/{username}/{kind}/{code}/")

        print(f"'{user["username"]}' have {len(links)} media on '{link}':")
        for link in links:
            print(f"- {link}")

        out = pathlib.Path(f"./out/{user["username"]}/page_info.json")
        out.parent.mkdir(exist_ok=True, parents=True)

        out.write_text(json.dumps({"links": links}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
