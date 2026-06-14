import json
import httpx
import pathlib
from typing import Any, Callable

from env import load_env


def dict_get(root: dict, *paths: str | int) -> Any:
    curr = root
    total = len(paths)
    count = 0

    while count + 1 < total:    # skip last path
        path = paths[count]

        if isinstance(curr, list):
            if not isinstance(path, int):
                raise TypeError(f"found array but path is not 'index', path: {count + 1}")
            curr_ = curr[path]
        else:
            curr_ = curr.get(path)

        if curr_ is None:
            raise ValueError(f"missing chainable path '{path}'")

        if not isinstance(curr_, (dict, list)):
            raise TypeError(f"expecting a chainable value got: {type(curr_)}")

        count += 1
        curr = curr_

    path = paths[-1]
    if isinstance(curr, list):
        if not isinstance(path, int):
            raise TypeError(f"found array but path is not 'index', path: {total}")
        result = curr[path]
    else:
        result = curr.get(path)

    return result

def dict_try(root: dict, *keys: str) -> Any:
    for key in keys:
        if key in root:
            return root[key]

def download_file(client: httpx.Client, url: str, path: pathlib.Path, callback: Callable[[int, int], None]) -> pathlib.Path:
    path = pathlib.Path(path)
    tmp_path = path.with_suffix(path.suffix + ".part")
    path.parent.mkdir(parents=True, exist_ok=True)
    success = False

    try:
        with client.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", -1))
            done = 0

            if (total > 0 and path.exists() and path.stat().st_size == total):
                if callback:
                    callback(total, total)
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)

                success = True
                return path

            with tmp_path.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    done += len(chunk)
                    if callback is not None:
                        callback(done, total)

        tmp_path.replace(path)
        success = True
        return path
    finally:
        if not success:
            tmp_path.unlink(missing_ok=True)

def expect(resp: httpx.Response, content_type: str):
    _ctype: str = resp.headers.get("Content-Type", "")
    if content_type not in _ctype:
        raise TypeError(f"unexpected content type '{_ctype}' in response (want: {content_type})")

def validate_json_response(resp: httpx.Response, expected_key: str | None = None, status_key: str | None = "status") -> dict:
    expect(resp, "json")

    data = json.loads(resp.text)
    if resp.status_code != 200 or (status_key and data.get(status_key, "") != "ok"):
        raise RuntimeError(
            f"[{resp.status_code}] API errored out:\n{resp.text}"
        )

    if expected_key:
        if expected_key not in data:
            raise ValueError(f"[{resp.status_code}] Response does not contain '{expected_key}' key")
        data = data[expected_key]

    return data

def graphql_query(client: httpx.Client, doc_id: str | int, variables: dict[str, object], expected_key: str | None = None) -> dict:
    query = {
        "doc_id": str(doc_id),
        "variables": json.dumps(variables),
    }

    resp = client.get("/graphql/query/", params=query, follow_redirects=True)
    return validate_json_response(resp, expected_key=expected_key)


class _Utils:
    def __init__(self) -> None:
        raise NotImplementedError()

class Writer(_Utils):
    _out_path: pathlib.Path = pathlib.Path.cwd() / "out"

    @classmethod
    def set_path(cls, out_dir: pathlib.Path) -> None:
        cls._out_path = out_dir

        cls._out_path.mkdir(exist_ok=True, parents=True)
        setattr(cls, "_out_path", True)

    @classmethod
    def json_out(cls, filename: str, **kwarg) -> None:
        if not getattr(cls, "_out_exists", cls._out_path.exists()):
            cls._out_path.mkdir(exist_ok=True, parents=True)
            setattr(cls, "_out_exists", True)

        loaded: list | dict = {}
        try:
            loaded = json.loads(cls._out_path.read_text())
        except Exception:
            pass

        if isinstance(loaded, dict):
            loaded.update(kwarg)
        elif isinstance(loaded, list):
            loaded.append({**kwarg})

        (cls._out_path / filename).write_text(json.dumps(loaded, indent=4, ensure_ascii=False))

class Clients(_Utils):
    _BASE_HEADERS: dict[str, str] = {
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
    _ENV_COOKIES: dict[str, str] = load_env()
    
    @classmethod
    def normal(cls) -> httpx.Client:
        return httpx.Client(base_url="https://instagram.com", headers=cls._BASE_HEADERS, follow_redirects=True)

    @classmethod
    def authed(cls) -> httpx.Client:
        client = cls.normal()
        client.cookies.update(cls._ENV_COOKIES)

        return client
