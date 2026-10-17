import pathlib
import sys

from polaris.utils import extract_json, retrive_content, save_json, get_client

def main():
    if len(sys.argv) < 2:
        raise ValueError("page link in required!")

    link = sys.argv.pop()
    with get_client() as client:
        is_file = not pathlib.Path(link).exists()
        text, path = retrive_content(link, client)

        user = extract_json(text, "xig_user_by_username",
                            'adp_PolarisLoggedOutDesktopWWWProfileRootContentQueryRelayPreloader')["xig_user_by_username"]
        data = extract_json(text, "xig_user_by_username",
                            'adp_PolarisLoggedOutDesktopWWWProfile(?:Reels|Posts)TabContentQueryRelayPreloader')["xig_user_by_username"]
        if not (is_file and path.with_suffix(".json").exists()):
            save_json({"user": user, "data": data}, path.with_suffix(".json"))

        is_posts = "polaris_ordered_timeline_connection" in data
        username, kind = user["username"], "p" if is_posts else "reel"
        nodes = data["polaris_ordered_timeline_connection" if is_posts else "polaris_clips_connection"]["edges"]

        links = list(map(
            lambda node: f"https://www.instagram.com/{username}/{kind}/{node["code"]}/",
            map(lambda conn: conn["node"], nodes)
        ))

        print(f"'{username}' have {len(links)} media on '{link}':")
        for link in links: print("+", link)

        save_json({"links": links}, pathlib.Path(f"./out/{username}/{'posts' if is_posts else 'reels'}_info.json"))

if __name__ == "__main__":
    main()
