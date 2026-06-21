import time
import random
from sys import argv

from consts import DocIds
from utils import Clients, Writer, dict_get, graphql_query

def main():
    if (len(argv) < 2):
        raise ValueError("username required!")

    username = argv.pop()
    with Clients.authed() as client:
        after: str | None = None
        has_next = True
        posts = []

        while has_next:
            variables = {
                "after": after,
                "before": None,
                "data": {
                    "count": 18,
                    "include_reel": False,
                    "include_chaining": True,
                    "include_feed_video": True,
                    "include_media_chaining": True,
                },
                "first": 18,
                "last": None,
                "username": username,
                "__relay_internal__pv__PolarisImmersiveFeedChainingEnabledrelayprovider": True,
                "__relay_internal__pv__PolarisAIGMAccountLabelEnabledrelayprovider": False,
            }

            resp = graphql_query(client, DocIds.USER_FEED, variables, expected_key="data")
            user_media = dict_get(resp, "xdt_api__v1__feed__user_timeline_graphql_connection")

            after = dict_get(user_media, "page_info", "end_cursor")
            has_next = dict_get(user_media, "page_info", "has_next_page")

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
                Writer.json_out(f"{username}-posts.json", posts=posts, edges=edges)

            time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    main()
