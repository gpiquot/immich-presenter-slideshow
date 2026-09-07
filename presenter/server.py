#!/usr/bin/env python3
import os
import html
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response

load_dotenv("/opt/immich_presenter/.env")

IMMICH_URL = os.environ["IMMICH_URL"].rstrip("/")
IMMICH_API_KEY = os.environ["IMMICH_API_KEY"]
PORT = int(os.environ.get("PORT", "8088"))
BASE_PATH = os.environ.get("BASE_PATH", "/").strip()
PRESENTER_TOKEN = os.environ.get("PRESENTER_TOKEN", "")
DEFAULT_SHARE_KEY = os.environ.get("DEFAULT_SHARE_KEY", "").strip()
XMP_CONTAINER_PREFIX = os.environ.get("XMP_CONTAINER_PREFIX", "/data").rstrip("/")
XMP_HOST_PREFIX = os.environ.get("XMP_HOST_PREFIX", "/opt/immich_data").rstrip("/")

# Optionnel, pour conserver un mode album local si tu l'avais encore dans .env.
ALBUM_NAME = os.environ.get("ALBUM_NAME", "").strip()

if not BASE_PATH.startswith("/"):
    BASE_PATH = "/" + BASE_PATH
if not BASE_PATH.endswith("/"):
    BASE_PATH += "/"

HEADERS = {
    "Accept": "application/json",
    "x-api-key": IMMICH_API_KEY,
}

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
    static_url_path=f"{BASE_PATH.rstrip('/')}/static",
)

_cache_by_source = {}


def immich_get(path: str, headers=None, params=None):
    url = IMMICH_URL + path
    r = requests.get(url, headers=headers or HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def immich_put(path: str, payload: dict):
    url = IMMICH_URL + path
    r = requests.put(
        url,
        headers={**HEADERS, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json() if r.content else {}


def get_presenter_ok():
    token = request.args.get("presenter", "")
    return bool(PRESENTER_TOKEN) and token == PRESENTER_TOKEN


def get_share_key():
    return request.args.get("share", "").strip() or DEFAULT_SHARE_KEY

def container_path_to_host_path(path):
    if not path:
        return ""

    if path.startswith(XMP_CONTAINER_PREFIX + "/"):
        return XMP_HOST_PREFIX + path[len(XMP_CONTAINER_PREFIX):]

    return path


def read_xmp_description(original_path):
    host_path = container_path_to_host_path(original_path)
    if not host_path:
        return ""

    xmp_path = host_path + ".xmp"

    if not os.path.exists(xmp_path):
        return ""

    try:
        tree = ET.parse(xmp_path)
        root = tree.getroot()

        namespaces = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "tiff": "http://ns.adobe.com/tiff/1.0/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        }

        for tag in [
            ".//dc:description/rdf:Alt/rdf:li",
            ".//tiff:ImageDescription/rdf:Alt/rdf:li",
        ]:
            node = root.find(tag, namespaces)
            if node is not None and node.text:
                return html.unescape(node.text.strip())

    except Exception:
        return ""

    return ""

def asset_to_simple(asset):
    original_path = asset.get("originalPath", "")
    xmp_description = read_xmp_description(original_path)

    return {
        "id": asset["id"],
        "originalFileName": asset.get("originalFileName", ""),
        "originalPath": original_path,
        "description": xmp_description or asset.get("description") or "",
        "type": asset.get("type", ""),
    }

def flatten_shared_link_assets(shared_link):
    assets = []

    # Cas le plus courant : assets directement présents dans le partage
    for asset in shared_link.get("assets", []) or []:
        if asset.get("type") == "IMAGE":
            assets.append(asset_to_simple(asset))

    # Cas partage d'album : l'album contient lui-même les assets
    album = shared_link.get("album")
    if album:
        for asset in album.get("assets", []) or []:
            if asset.get("type") == "IMAGE":
                assets.append(asset_to_simple(asset))

    # Déduplication conservant l'ordre
    seen = set()
    unique = []
    for asset in assets:
        if asset["id"] not in seen:
            unique.append(asset)
            seen.add(asset["id"])

    return unique


def get_assets_from_share(share_key):
    cache_key = f"share:{share_key}"
    if cache_key in _cache_by_source:
        return _cache_by_source[cache_key]

    # Endpoint utilisé par Immich pour accéder au partage public.
    # Les versions récentes utilisent /shared-links/me?key=...
    shared_link = immich_get(
        "/shared-links/me",
        headers={"Accept": "application/json"},
        params={"key": share_key},
    )

    assets = flatten_shared_link_assets(shared_link)

    # Si c'est un partage d'album, Immich peut renvoyer assetCount mais pas la liste des assets.
    # Dans ce cas, on récupère le détail complet de l'album via l'API authentifiée.
    album = shared_link.get("album")
    if not assets and album and album.get("id"):
        album_details = immich_get(f"/albums/{album['id']}")
        for asset in album_details.get("assets", []) or []:
            if asset.get("type") == "IMAGE":
                assets.append(asset_to_simple(asset))

    assets.sort(key=lambda a: a.get("originalFileName", "").lower())

    result = {
        "sourceName": shared_link.get("description")
        or shared_link.get("album", {}).get("albumName")
        or "Partage Immich",
        "assets": assets,
        "allowedAssetIds": {asset["id"] for asset in assets},
    }
    _cache_by_source[cache_key] = result
    return result


def get_album_by_name(album_name):
    albums = immich_get("/albums")
    for album in albums:
        if album.get("albumName") == album_name:
            return album
    raise RuntimeError(f"Album introuvable : {album_name}")


def get_assets_from_album(album_name):
    cache_key = f"album:{album_name}"
    if cache_key in _cache_by_source:
        return _cache_by_source[cache_key]

    album = get_album_by_name(album_name)
    details = immich_get(f"/albums/{album['id']}")
    assets = []

    for asset in details.get("assets", []) or []:
        if asset.get("type") == "IMAGE":
            assets.append(asset_to_simple(asset))

    result = {
        "sourceName": album_name,
        "assets": assets,
        "allowedAssetIds": {asset["id"] for asset in assets},
    }

    _cache_by_source[cache_key] = result
    return result


def get_current_source():
    share_key = get_share_key()

    if share_key:
        return get_assets_from_share(share_key)

    # Mode de secours local uniquement. Ne pas exposer ce mode sur Internet.
    if ALBUM_NAME:
        return get_assets_from_album(ALBUM_NAME)

    raise RuntimeError("Aucun partage fourni. Utilise ?share=CLE_DU_PARTAGE_IMMICH")


def ensure_asset_allowed(asset_id):
    source = get_current_source()
    if asset_id not in source["allowedAssetIds"]:
        raise RuntimeError("Asset non autorisé pour ce partage")
    return source


@app.route(f"{BASE_PATH}")
def index():
    return render_template("index.html", base_path=BASE_PATH)


@app.route(f"{BASE_PATH}api/assets")
def api_assets():
    try:
        source = get_current_source()
        return jsonify({
            "albumName": source["sourceName"],
            "count": len(source["assets"]),
            "assets": source["assets"],
            "canEdit": get_presenter_ok(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f"{BASE_PATH}api/assets/<asset_id>/image")
def api_asset_image(asset_id):
    try:
        ensure_asset_allowed(asset_id)
        url = IMMICH_URL + f"/assets/{asset_id}/original"
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "application/octet-stream")
        return Response(r.iter_content(chunk_size=65536), content_type=content_type)
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@app.route(f"{BASE_PATH}api/assets/<asset_id>/thumbnail")
def api_asset_thumbnail(asset_id):
    try:
        ensure_asset_allowed(asset_id)
        url = IMMICH_URL + f"/assets/{asset_id}/thumbnail"
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "image/webp")
        return Response(r.iter_content(chunk_size=65536), content_type=content_type)
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@app.route(f"{BASE_PATH}api/assets/<asset_id>/description", methods=["PUT"])
def api_asset_description(asset_id):
    if not get_presenter_ok():
        return jsonify({"error": "Edition non autorisée"}), 403

    try:
        source = ensure_asset_allowed(asset_id)

        data = request.get_json(force=True)
        description = data.get("description", "")

        immich_put(f"/assets/{asset_id}", {"description": description})

        for asset in source["assets"]:
            if asset["id"] == asset_id:
                asset["description"] = description
                break

        return jsonify({"ok": True, "description": description})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"Immich Presenter démarré sur http://0.0.0.0:{PORT}{BASE_PATH}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
