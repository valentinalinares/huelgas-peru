from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "anuarios"
DEFAULT_PORTAL_URL = "https://www2.trabajo.gob.pe/estadisticas/anuarios-estadisticos/"
DEFAULT_MANIFEST_OUTPUT = ROOT / "anuarios" / "manifest.generated.csv"
CHUNK_SIZE = 1024 * 256
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": DEFAULT_PORTAL_URL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rastrea el portal oficial de anuarios MTPE, descarga los ZIP y los descomprime."
    )
    parser.add_argument(
        "--portal-url",
        default=DEFAULT_PORTAL_URL,
        help="URL de la página índice de anuarios.",
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=DEFAULT_TARGET,
        help="Carpeta raíz donde se guardarán y extraerán los anuarios.",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=DEFAULT_MANIFEST_OUTPUT,
        help="Ruta donde se guardará el manifest generado desde el portal.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescribe ZIPs existentes y vuelve a extraer.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout por request en segundos.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra qué detecta y qué haría, sin descargar.",
    )
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        help="Años específicos a descargar. Si se omite, intenta todos los detectados.",
    )
    return parser.parse_args()


def request_text(url: str, timeout: int) -> str:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def request_binary(url: str, timeout: int) -> bytes:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.content


def clean_url(url: str) -> str:
    url = url.strip()
    if url.startswith("http:s//"):
        return "https://" + url[len("http:s//") :]
    if url.startswith("http://"):
        return "https://" + url[len("http://") :]
    return url


def year_from_text(text: str) -> int | None:
    matches = [int(value) for value in re.findall(r"(19\d{2}|20\d{2})", text)]
    valid = [value for value in matches if 1990 <= value <= 2026]
    return valid[-1] if valid else None


def filename_from_url(url: str) -> str:
    path = urlparse(url).path
    return unquote(Path(path).name) or "download.zip"


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_manifest(rows: list[dict[str, object]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["year", "zip_url", "zip_filename", "source_page", "source_type"]
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: int(item["year"])):
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_gob_page(publication_url: str, timeout: int) -> dict[str, object] | None:
    html = request_text(publication_url, timeout)
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for anchor in soup.find_all("a", href=True):
        href = clean_url(anchor["href"])
        if ".zip" in href.lower():
            candidates.append(href)
    if not candidates:
        return None
    year = year_from_text(publication_url) or year_from_text(soup.get_text(" ", strip=True))
    if year is None:
        return None
    zip_url = candidates[0]
    return {
        "year": year,
        "zip_url": zip_url,
        "zip_filename": filename_from_url(zip_url),
        "source_page": publication_url,
        "source_type": "gob_page",
    }


def parse_portal(portal_url: str, timeout: int) -> list[dict[str, object]]:
    html = request_text(portal_url, timeout)
    soup = BeautifulSoup(html, "html.parser")

    rows_by_year: dict[int, dict[str, object]] = {}

    for anchor in soup.find_all("a", href=True):
        href = clean_url(anchor["href"])
        href_lower = href.lower()

        if "gob.pe/institucion/mtpe/informes-publicaciones" in href_lower:
            parsed = parse_gob_page(href, timeout)
            if parsed:
                rows_by_year[int(parsed["year"])] = parsed
            continue

        if ".zip" not in href_lower:
            continue

        if "issuu.com" in href_lower:
            continue

        year = year_from_text(href)
        if year is None:
            continue
        rows_by_year[year] = {
            "year": year,
            "zip_url": href,
            "zip_filename": filename_from_url(href),
            "source_page": portal_url,
            "source_type": "direct_zip",
        }

    return [rows_by_year[year] for year in sorted(rows_by_year)]


def safe_extract_zip(data: bytes, destination_dir: Path) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            member_path = PurePosixPath(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"Ruta insegura dentro del ZIP: {member.filename}")
            target_path = destination_dir / Path(*member_path.parts)
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, target_path.open("wb") as dst:
                dst.write(src.read())


def download_and_extract(
    row: dict[str, object],
    target_root: Path,
    overwrite: bool,
    timeout: int,
    dry_run: bool,
) -> None:
    year = int(row["year"])
    year_dir = target_root / str(year)
    zip_filename = str(row["zip_filename"])
    zip_path = year_dir / zip_filename

    if zip_path.exists() and not overwrite:
        print(f"[skip] {year} | {zip_filename} ya existe")
        return

    if dry_run:
        print(f"[dry-run] {year} | {row['zip_url']} -> {zip_path}")
        return

    print(f"[download] {year} | {row['zip_url']}")
    data = request_binary(str(row["zip_url"]), timeout)
    year_dir.mkdir(parents=True, exist_ok=True)
    zip_path.write_bytes(data)
    print(f"[saved] {zip_path} | sha256={sha256_of_bytes(data)}")
    safe_extract_zip(data, year_dir)
    print(f"[extracted] {year_dir}")


def main() -> None:
    args = parse_args()
    target_root = args.target_root.resolve()
    manifest_out = args.manifest_out.resolve()

    all_rows = parse_portal(args.portal_url, args.timeout)
    save_manifest(all_rows, manifest_out)
    print(f"[manifest] {manifest_out}")

    rows = all_rows
    if args.years:
        selected = set(args.years)
        rows = [row for row in rows if int(row["year"]) in selected]

    if not rows:
        print("[download] No se detectaron anuarios descargables.")
        return

    for row in rows:
        download_and_extract(
            row=row,
            target_root=target_root,
            overwrite=args.overwrite,
            timeout=args.timeout,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
