from httpx import Client
import time
import random
from sys import argv

from consts import DocIds
from utils import Clients, Writer, dict_get, dict_try, graphql_query

def get_user_id(client: Client, username: str) -> str:
    variables = {
        "after": None,
        "before": None,
        "data": {
            "count": 1,
        },
        "first": 1,
        "last": None,
        "username": username,
        "__relay_internal__pv__PolarisImmersiveFeedChainingEnabledrelayprovider": True,
        "__relay_internal__pv__PolarisAIGMAccountLabelEnabledrelayprovider": False,
    }

    resp = graphql_query(client, DocIds.USER_FEED, variables, expected_key="data")
    user = dict_get(resp, "xdt_api__v1__feed__user_timeline_graphql_connection", "edges", 0, "node", "user")

    return dict_try(user, "pk", "id")

def main():
    if (len(argv) < 2):
        raise ValueError("username required!")

    username = argv.pop()

    with Clients.authed() as client:
        user_id: str = get_user_id(client, username)
        after: str | None = None
        has_next = True
        reels = []

        while has_next:
            variables = {
                "after": after,
                "before": None,
                "data": {
                    "page_size": 18,
                    "target_user_id": user_id,
                    "include_feed_video": False,
                },
                "first": 3,
                "last": None,
            }

            resp = graphql_query(client, DocIds.USER_CLIPS, variables, expected_key="data")
            user_media = dict_get(resp, "xdt_api__v1__clips__user__connection_v2")

            after = dict_get(user_media, "page_info", "end_cursor")
            has_next = dict_get(user_media, "page_info", "has_next_page")

            edges = []
            try:
                for edge in filter(bool, map(
                    lambda edge: edge.get("node"),
                    user_media["edges"],
                )):
                    edge["media"]["__typename"] = edge["__typename"]
                    edges.append(edge["media"])
                print("extracted", len(edges), "total", len(reels) + len(edges))
            except Exception as e:
                print("error", e)
                raise
            finally:
                edges = sorted(edges, key=lambda node: node.get("taken_at", 0), reverse=True)
                reels = sorted(reels + edges, key=lambda node: node.get("taken_at", 0), reverse=True)
                Writer.json_out(f"{username}-reels.json", reels=reels, edges=edges)

            time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    main()
