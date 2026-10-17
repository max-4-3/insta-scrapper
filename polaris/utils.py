import re
import json
from pathlib import Path

from httpx import Client

from polaris.consts import HEADERS

temp = Path("./temp/")


def get_client() -> Client:
    return Client(follow_redirects=True, headers=HEADERS)

def retrive_content(link: str, client: Client) -> tuple[str, Path]:
    is_file = not Path(link).exists()
    if not is_file:
        page = client.get(link, follow_redirects=True, headers={**HEADERS, "Referer": link})
        page.raise_for_status()
        print(f"[{page.status_code}] GET {link} [{len(page.history)}]")

        path = (temp / alnum_and_under(link)).with_suffix(".page")
        text = page.read().decode(errors="ignore")

        save_page(text, path)
    else:
        path = Path(link)
        text = path.read_text()

    print(f"[{is_file and '<' or '>'}-{len(text)}] {path}")
    return (text, path)

def save_page(page: str, path: Path):
    save_str(page, path, ctype="page")

def save_json(data, path: Path):
    save_str(json.dumps(data, indent=2, ensure_ascii=False), path, ctype="json")

def save_str(content: str, path: Path, ctype: str = "text"):
    path.parent.mkdir(exist_ok=True, parents=True)
    if not path.suffix:
        path = path.with_suffix(f".{ctype}")

    path.write_text(content)

def alnum_and_under(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', '-', name)

def extract_json(data: str, key: str, prefix: str | None = None) -> dict:
    # 1. Locate where the JSON object begins
    pattern = re.compile(
        ''.join([
            rf'{prefix}.*?' if prefix else '',
            r'(\{"%s"\s*:\s*)' % key
        ])
    )

    srch = pattern.search(data)
    if not srch: return {}

    # 2. Extract starting from the matched '{' of the last capturing group
    start_idx = srch.start(len(srch.groups()))
    decoder = json.JSONDecoder()

    try:
        # raw_decode parses a valid JSON object starting at start_idx
        # and returns a tuple: (parsed_dict, end_index_position)
        obj, _ = decoder.raw_decode(data, idx=start_idx)
        return obj
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return {}
