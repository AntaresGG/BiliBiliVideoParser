"""Extract normalized Bilibili metadata, subtitles, and audience signals.

Examples:
    python bilibili_extract.py BV1xx411c7mD
    python bilibili_extract.py "https://www.bilibili.com/video/BV...?p=2" --out source.json
    python bilibili_extract.py BV... --include-danmaku --out source.json
    python bilibili_extract.py --self-check

The script uses only the Python standard library. Authentication is opt-in via
--use-env-cookie and BILI_SESSDATA/BILI_JCT/BILI_BUVID3 environment variables.
Secrets are sent as request cookies but never included in output.
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
import zlib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

API_ROOT = "https://api.bilibili.com"
SELF_CHECK_BVID = "BV1xx411c7mD"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
)


class ParserError(RuntimeError):
    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage


class BilibiliClient:
    def __init__(self, use_env_cookie: bool = False, retries: int = 3) -> None:
        self.retries = retries
        self.cookie = self._load_cookie() if use_env_cookie else None

    @staticmethod
    def _load_cookie() -> str:
        if not os.environ.get("BILI_SESSDATA"):
            raise ParserError(
                "authentication",
                "--use-env-cookie requires BILI_SESSDATA in the environment.",
            )
        names = {
            "BILI_SESSDATA": "SESSDATA",
            "BILI_JCT": "bili_jct",
            "BILI_BUVID3": "buvid3",
        }
        pairs = [f"{cookie_name}={os.environ[env_name]}" for env_name, cookie_name in names.items() if os.environ.get(env_name)]
        return "; ".join(pairs)

    def _headers(self, referer: str | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Referer": referer or "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def request_bytes(self, url: str, stage: str, referer: str | None = None) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = Request(url, headers=self._headers(referer))
                with urlopen(request, timeout=30) as response:
                    payload = response.read()
                    encoding = response.headers.get("Content-Encoding", "").lower()
                    if encoding == "gzip":
                        return gzip.decompress(payload)
                    if encoding == "deflate":
                        try:
                            return zlib.decompress(payload)
                        except zlib.error:
                            return zlib.decompress(payload, -zlib.MAX_WBITS)
                    return payload
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {412, 429, 500, 502, 503, 504}:
                    break
            except URLError as exc:
                last_error = exc
            if attempt + 1 < self.retries:
                time.sleep(0.6 * (2**attempt))
        raise ParserError(stage, f"Request failed for {url}: {last_error}")

    def get_json(self, url: str, stage: str, referer: str | None = None) -> dict[str, Any]:
        try:
            payload = json.loads(self.request_bytes(url, stage, referer).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ParserError(stage, f"Invalid JSON response from {url}: {exc}") from exc
        if isinstance(payload, dict) and payload.get("code") not in (None, 0):
            raise ParserError(stage, f"Bilibili API error {payload.get('code')}: {payload.get('message')}")
        return payload

    def resolve_redirect(self, url: str) -> str:
        request = Request(url, headers=self._headers())
        try:
            with urlopen(request, timeout=30) as response:
                return response.geturl()
        except (HTTPError, URLError) as exc:
            raise ParserError("resolve", f"Could not resolve short link: {exc}") from exc


def normalize_subtitle_url(value: str) -> str:
    if value.startswith("//"):
        return f"https:{value}"
    return value


def parse_reference(value: str) -> dict[str, Any]:
    bvid_match = re.search(r"(BV[0-9A-Za-z]+)", value, re.IGNORECASE)
    aid_match = re.search(r"(?:^|/|\b)av(\d+)", value, re.IGNORECASE)
    ep_match = re.search(r"(?:^|/)ep(\d+)", value, re.IGNORECASE)
    season_match = re.search(r"(?:^|/)ss(\d+)", value, re.IGNORECASE)
    query = parse_qs(urlparse(value).query) if "://" in value else {}
    page = int(query.get("p", [1])[0]) if query.get("p", ["1"])[0].isdigit() else 1
    if bvid_match:
        return {"bvid": bvid_match.group(1), "page": page}
    if aid_match:
        return {"aid": int(aid_match.group(1)), "page": page}
    if ep_match:
        return {"ep_id": int(ep_match.group(1)), "page": 1}
    if season_match:
        return {"season_id": int(season_match.group(1)), "page": 1}
    raise ParserError("resolve", "Input must contain a BV ID, av ID, ep ID, ss ID, or Bilibili URL.")


async def resolve_input(client: BilibiliClient, value: str, requested_page: int | None) -> dict[str, Any]:
    resolved = value
    host = urlparse(value).hostname or ""
    if host.lower() in {"b23.tv", "bili2233.cn"}:
        resolved = await asyncio.to_thread(client.resolve_redirect, value)

    reference = parse_reference(resolved)
    reference["input"] = value
    reference["resolved_url"] = resolved
    if requested_page is not None:
        reference["page"] = requested_page

    if "ep_id" in reference or "season_id" in reference:
        key = "ep_id" if "ep_id" in reference else "season_id"
        query = urlencode({key: reference[key]})
        payload = await asyncio.to_thread(
            client.get_json,
            f"{API_ROOT}/pgc/view/web/season?{query}",
            "season",
        )
        episodes = payload.get("result", {}).get("episodes", [])
        if key == "ep_id":
            episode = next((item for item in episodes if item.get("id") == reference[key]), None)
        else:
            episode = episodes[0] if episodes else None
        if not episode or not episode.get("bvid"):
            raise ParserError("season", "Could not resolve the requested episode or season to a BVID.")
        reference["bvid"] = episode["bvid"]
        reference["episode_id"] = episode.get("id")
    return reference


def choose_subtitle(items: list[dict[str, Any]], requested_language: str | None) -> dict[str, Any] | None:
    if not items:
        return None
    if requested_language:
        target = requested_language.lower()
        match = next(
            (
                item
                for item in items
                if target in {str(item.get("lan", "")).lower(), str(item.get("lan_doc", "")).lower()}
            ),
            None,
        )
        if match:
            return match

    def rank(item: dict[str, Any]) -> tuple[int, int]:
        language = str(item.get("lan", "")).lower()
        is_ai = bool(item.get("ai_type")) or language.startswith("ai-")
        chinese = language in {"zh-cn", "zh-hans", "zh", "ai-zh"}
        return (1 if is_ai else 0, 0 if chinese else 1)

    return min(items, key=rank)


def normalize_segments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    segments = []
    for item in payload.get("body", []) or []:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        segments.append(
            {
                "start": round(float(item.get("from", 0)), 3),
                "end": round(float(item.get("to", item.get("from", 0))), 3),
                "text": content,
            }
        )
    return segments


def parse_danmaku(payload: bytes, limit: int) -> dict[str, Any]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ParserError("danmaku", f"Invalid danmaku XML: {exc}") from exc

    entries: list[dict[str, Any]] = []
    buckets: Counter[int] = Counter()
    repeated: Counter[str] = Counter()
    total = 0
    for node in root.findall("d"):
        text = (node.text or "").strip()
        if not text:
            continue
        total += 1
        fields = node.attrib.get("p", "0").split(",")
        try:
            second = float(fields[0])
        except (ValueError, IndexError):
            second = 0.0
        buckets[int(second // 30) * 30] += 1
        repeated[re.sub(r"\s+", "", text)] += 1
        if len(entries) < limit:
            entries.append({"time": round(second, 3), "text": text})

    hotspots = [
        {"start": second, "end": second + 30, "count": count}
        for second, count in buckets.most_common(8)
    ]
    repeated_items = [
        {"text": text, "count": count}
        for text, count in repeated.most_common(12)
        if count > 1
    ]
    return {
        "fetched_count": total,
        "sampled": len(entries),
        "entries": entries,
        "hotspots_30s": hotspots,
        "repeated_comments": repeated_items,
        "interpretation_warning": "Danmaku reflects audience reaction, not factual verification.",
    }


async def safe_json(
    client: BilibiliClient,
    url: str,
    stage: str,
    referer: str,
    warnings: list[str],
) -> dict[str, Any]:
    try:
        return await asyncio.to_thread(client.get_json, url, stage, referer)
    except ParserError as exc:
        warnings.append(f"{stage}: {exc}")
        return {}


async def extract(args: argparse.Namespace) -> dict[str, Any]:
    client = BilibiliClient(use_env_cookie=args.use_env_cookie, retries=args.retries)
    reference = await resolve_input(client, args.video, args.page)
    view_query = {"bvid": reference["bvid"]} if reference.get("bvid") else {"aid": reference["aid"]}
    view = await asyncio.to_thread(
        client.get_json,
        f"{API_ROOT}/x/web-interface/view?{urlencode(view_query)}",
        "view",
    )
    data = view.get("data", {})
    bvid = data.get("bvid")
    pages = data.get("pages", []) or [{"cid": data.get("cid"), "page": 1, "part": data.get("title")}]
    page_number = int(reference.get("page", 1))
    if page_number < 1 or page_number > len(pages):
        raise ParserError("page", f"Page {page_number} is outside the available range 1-{len(pages)}.")
    selected_page = pages[page_number - 1]
    cid = selected_page.get("cid")
    if not cid:
        raise ParserError("page", "Selected page does not contain a CID.")

    canonical_url = f"https://www.bilibili.com/video/{bvid}/"
    if len(pages) > 1:
        canonical_url = f"{canonical_url}?p={page_number}"
    warnings: list[str] = []
    referer = canonical_url
    player_url = f"{API_ROOT}/x/player/wbi/v2?{urlencode({'bvid': bvid, 'cid': cid})}"
    tags_url = f"{API_ROOT}/x/tag/archive/tags?{urlencode({'bvid': bvid})}"
    player, tags_payload = await asyncio.gather(
        safe_json(client, player_url, "player", referer, warnings),
        safe_json(client, tags_url, "tags", referer, warnings),
    )

    subtitle_items = player.get("data", {}).get("subtitle", {}).get("subtitles", []) or []
    subtitle = choose_subtitle(subtitle_items, args.subtitle_language)
    segments: list[dict[str, Any]] = []
    source_type = "none"
    selected_language = None
    if subtitle:
        subtitle_url = normalize_subtitle_url(subtitle.get("subtitle_url") or subtitle.get("subtitle_url_v2") or "")
        if subtitle_url:
            try:
                subtitle_payload = await asyncio.to_thread(
                    client.get_json,
                    subtitle_url,
                    "subtitle",
                    referer,
                )
                segments = normalize_segments(subtitle_payload)
            except ParserError as exc:
                warnings.append(f"subtitle: {exc}")
        selected_language = subtitle.get("lan") or subtitle.get("lan_doc")
        is_ai = bool(subtitle.get("ai_type")) or str(selected_language).lower().startswith("ai-")
        source_type = "ai_subtitle" if is_ai else "official_subtitle"
    if not segments:
        source_type = "none"
        warnings.append("No accessible subtitle text; use audio transcription fallback when content is required.")

    audience_signals = None
    if args.include_danmaku:
        try:
            xml = await asyncio.to_thread(
                client.request_bytes,
                f"{API_ROOT}/x/v1/dm/list.so?oid={cid}",
                "danmaku",
                referer,
            )
            audience_signals = {"danmaku": parse_danmaku(xml, args.danmaku_limit)}
        except ParserError as exc:
            warnings.append(f"danmaku: {exc}")

    tags = [item.get("tag_name") for item in tags_payload.get("data", []) if item.get("tag_name")]
    fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    stat = data.get("stat", {})
    published_at_unix = data.get("pubdate")
    published_at = (
        datetime.fromtimestamp(published_at_unix, UTC).isoformat().replace("+00:00", "Z")
        if published_at_unix
        else None
    )
    part_duration = selected_page.get("duration") or data.get("duration") or 0
    coverage_seconds = segments[-1]["end"] - segments[0]["start"] if segments else 0
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "source": {
            "platform": "bilibili",
            "input": args.video,
            "resolved_url": reference.get("resolved_url"),
            "canonical_url": canonical_url,
            "fetched_at": fetched_at,
            "authenticated": bool(client.cookie),
        },
        "metadata": {
            "bvid": bvid,
            "aid": data.get("aid"),
            "title": data.get("title"),
            "description": data.get("desc"),
            "uploader": data.get("owner"),
            "published_at": published_at,
            "published_at_unix": published_at_unix,
            "duration_seconds": data.get("duration"),
            "category": data.get("tname"),
            "tags": tags,
            "stats": {
                "view": stat.get("view"),
                "danmaku": stat.get("danmaku"),
                "reply": stat.get("reply"),
                "favorite": stat.get("favorite"),
                "coin": stat.get("coin"),
                "share": stat.get("share"),
                "like": stat.get("like"),
            },
            "pages": [
                {
                    "page": item.get("page"),
                    "cid": item.get("cid"),
                    "title": item.get("part"),
                    "duration_seconds": item.get("duration"),
                }
                for item in pages
            ],
        },
        "selection": {
            "page": page_number,
            "cid": cid,
            "part_title": selected_page.get("part"),
        },
        "content": {
            "source_type": source_type,
            "language": selected_language,
            "segments": segments,
            "transcript": "\n".join(item["text"] for item in segments),
        },
        "source_status": {
            "content_source": source_type,
            "segment_count": len(segments),
            "coverage_seconds": round(coverage_seconds, 3),
            "coverage_ratio": round(min(1.0, coverage_seconds / part_duration), 4)
            if part_duration
            else None,
            "confidence": {
                "official_subtitle": "high",
                "ai_subtitle": "medium",
                "none": "unavailable",
            }[source_type],
        },
        "audience_signals": audience_signals,
        "analysis": None,
        "diagnostics": {
            "backend": "native-api",
            "warnings": warnings,
            "subtitle_tracks": [
                {
                    "language": item.get("lan"),
                    "label": item.get("lan_doc"),
                    "is_ai": bool(item.get("ai_type")) or str(item.get("lan", "")).startswith("ai-"),
                }
                for item in subtitle_items
            ],
        },
    }
    return result


async def self_check(args: argparse.Namespace) -> dict[str, Any]:
    check_args = argparse.Namespace(
        video=SELF_CHECK_BVID,
        page=1,
        subtitle_language=None,
        include_danmaku=False,
        danmaku_limit=0,
        use_env_cookie=False,
        retries=args.retries,
    )
    result = await extract(check_args)
    metadata = result["metadata"]
    ok = metadata.get("bvid") == SELF_CHECK_BVID and bool(metadata.get("title"))
    return {
        "ok": ok,
        "fixture": SELF_CHECK_BVID,
        "checked_at": result["source"]["fetched_at"],
        "metadata": {"title": metadata.get("title"), "cid": result["selection"]["cid"]},
        "warnings": result["diagnostics"]["warnings"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", help="Bilibili URL, BV ID, av ID, ep ID, or ss ID")
    parser.add_argument("--page", type=int, help="1-based page/part number; URL ?p= is used by default")
    parser.add_argument("--subtitle-language", help="Preferred subtitle code or label")
    parser.add_argument("--include-danmaku", action="store_true", help="Include sampled danmaku and hotspots")
    parser.add_argument("--danmaku-limit", type=int, default=300, help="Maximum danmaku entries to retain")
    parser.add_argument("--use-env-cookie", action="store_true", help="Use opt-in BILI_* environment credentials")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--out", help="Optional UTF-8 JSON output path")
    parser.add_argument("--self-check", action="store_true", help="Run a live anonymous API health check")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.self_check:
            result = asyncio.run(self_check(args))
        else:
            if not args.video:
                parser.error("video is required unless --self-check is used")
            result = asyncio.run(extract(args))
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        print(text)
        return 0 if result.get("ok", True) else 1
    except ParserError as exc:
        print(
            json.dumps(
                {"ok": False, "stage": exc.stage, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
