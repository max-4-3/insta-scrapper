import time
import random
from sys import argv
from httpx import Client

from consts import DocIds
from utils import Clients, Writer, dict_get, dict_try, graphql_query

def get_user_id(client: Client, username: str) -> str:
    # it fails if the user hasn't posted any posts
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
    user = dict_get(resp, "xdt_api__v1__feed__user_timeline_graphql_connection", "edges", 0, "node", "user", "id")

    return dict_try(user, "fk", "id")

def main():
    if (len(argv) < 2):
        raise ValueError("username required!")

    username = argv.pop()

    with Clients.normal() as client:
        user_id: str = get_user_id(client, username) if not username.isdigit() else username
        after: str | None = None
        has_next = True
        highlights = []

        while has_next:
            variables = {
                "after": after,
                "before": None,
                "first": 3,
                "last": None,
                "user_id": user_id,
            }

            resp = graphql_query(client, DocIds.USER_HIGHLIGHT, variables, expected_key="data")
            highlight = dict_get(resp, "highlights")

            after = dict_get(highlight, "page_info", "end_cursor")
            has_next = dict_get(highlight, "page_info", "has_next_page")

            edges = []
            try:
                for edge in filter(bool, map(
                    lambda edge: edge.get("node"),
                    highlight["edges"],
                )):
                    edges.append(edge)
                print("extracted", len(edges), "total", len(highlights) + len(edges))
            except Exception as e:
                print("error", e)
                raise
            finally:
                edges = sorted(edges, key=lambda node: node.get("taken_at", 0), reverse=True)
                highlights = sorted(highlights + edges, key=lambda node: node.get("taken_at", 0), reverse=True)
                Writer.json_out(f"./{username}-highlights.json", highlights=highlights, edges=edges)

            time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    main()
