from httpx import Client
import json
import time
import random
from pathlib import Path
from sys import argv

from env import load_env

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
COOKIES = load_env()

def write(path: Path, **kwarg):
    loaded: list | dict = {}

    try:
        loaded = json.loads(path.read_text())
    except Exception:
        pass

    if isinstance(loaded, dict):
        loaded.update(kwarg)
    elif isinstance(loaded, list):
        loaded.append({**kwarg})

    path.write_text(json.dumps(loaded, indent=4, ensure_ascii=False))
    print(path, "updated!")

def main():
    if (len(argv) < 2):
        raise ValueError("username required!")

    username = argv.pop()

    with Client(base_url="https://www.instagram.com", headers=HEADERS, cookies=COOKIES, follow_redirects=True) as client:
        after: str | None = None
        has_next = True
        posts = []

        while has_next:
            variables = {
                "after": after,
                "before": None,
                "data": {
                    "count": 18,
                    "latest_reel_media": True,
                    "include_reel": True,
                    "include_chaining": True,
                    "include_feed_video": True,
                    "include_media_chaining": True,
                    "include_reel_media_seen_timestamp": True,
                },
                "first": 18,
                "last": None,
                "username": username,
                "__relay_internal__pv__PolarisImmersiveFeedChainingEnabledrelayprovider": True,
                "__relay_internal__pv__PolarisAIGMAccountLabelEnabledrelayprovider": False,
            }

            
            query = {
                "doc_id": "27242482582022127",
                "variables": json.dumps(variables),
            }
            path = "/graphql/query/"
            resp = client.request(
                "GET",
                path,
                params=query,
            )

            data = (
                json.loads(resp.text) if "json" in resp.headers.get("Content-Type", "") else {}
            )

            if resp.status_code != 200 or data.get("status", "") != "ok" or not data["data"]:
                raise RuntimeError(
                    f"[{resp.status_code}] unable to retrive media:\n{resp.text}"
                )

            user_media = data["data"][
                "xdt_api__v1__feed__user_timeline_graphql_connection"
            ]
            page_info = user_media["page_info"]

            after = page_info["end_cursor"]
            has_next = page_info["has_next_page"]

            edges = []
            try:
                for edge in map(
                    lambda edge: (
                        edge
                        if not isinstance(edge, dict)
                        or not ((node := edge.get("node")) and isinstance(node, dict))
                        else node
                    ),
                    user_media["edges"],
                ):
                    edges.append(edge)
                print("extracted", len(edges), "total", len(posts) + len(edges))
            except Exception as e:
                print("error", e)
                raise
            finally:
                edges = sorted(edges, key=lambda node: node.get("taken_at", 0), reverse=True)
                posts = sorted(posts + edges, key=lambda node: node.get("taken_at", 0), reverse=True)
                write(Path(f"./{username}.json"), posts=edges, total_posts=posts)

            time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    main()
