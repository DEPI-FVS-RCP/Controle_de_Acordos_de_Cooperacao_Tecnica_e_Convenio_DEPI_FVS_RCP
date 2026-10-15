"""Sincroniza CSVs publicados do Google Sheets com os CSVs estáticos do FAROL."""

import argparse
import csv
import io
import math
import os
import re
import shutil
import tempfile
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
FILES = ("tbl_instrumentos.csv", "tbl_aditivos.csv", "tbl_instituicoes_geo.csv")
WIDTHS = (26, 14, 7)
GEO_HEADER = ["nome", "cidade", "uf", "lat", "lon", "url", "sigla"]
DATE_COLUMNS = {FILES[0]: (7, 8, 12, 13, 24), FILES[1]: (6, 7, 9, 10)}


def _read_csv(text, delimiter):
    try:
        rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""),
                               delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise ValueError("CSV malformado") from exc
    return [row for row in rows if any(cell.strip() for cell in row)]


def _valid_date(value, label):
    if not value:
        return
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        raise ValueError("Data fora de DD/MM/AAAA em " + label)
    try:
        datetime.strptime(value, "%d/%m/%Y")
    except ValueError as exc:
        raise ValueError("Data inexistente em " + label) from exc


def _valid_url(value, label, allow_local=False):
    if not value:
        return
    if re.search(r"[\s\"'<>\\]", value):
        raise ValueError("Link inseguro em " + label)
    parts = urlsplit(value)
    if parts.scheme in ("http", "https") and parts.netloc:
        return
    if allow_local and not parts.scheme and not parts.netloc:
        path = parts.path
        if path.startswith("documentos/instrumentos/") and ".." not in path.split("/"):
            return
    raise ValueError("Protocolo de link inválido em " + label)


def _ids(rows, label, key_column=0):
    result = []
    for line, row in enumerate(rows, 2):
        value = row[key_column].strip()
        if not value:
            raise ValueError("ID vazio em " + label + " linha " + str(line))
        result.append(value)
    if len(set(result)) != len(result):
        raise ValueError("ID duplicado em " + label)
    return set(result)


def _validate(name, incoming, current, width):
    if name == FILES[2] and incoming and incoming[0] == GEO_HEADER:
        incoming = incoming[1:]
    if not incoming:
        raise ValueError("CSV vazio: " + name)
    for line, row in enumerate(incoming, 1):
        if len(row) != width:
            raise ValueError("Número de colunas incorreto em " + name + " linha " + str(line))
    if name != FILES[2]:
        if incoming[0] != current[0]:
            raise ValueError("Cabeçalho diferente em " + name)
        if len(incoming) < 2:
            raise ValueError("CSV vazio: " + name)
        for line, row in enumerate(incoming[1:], 2):
            for col in DATE_COLUMNS[name]:
                _valid_date(row[col].strip(), name + " linha " + str(line))
        old_ids = _ids(current[1:], name)
        new_ids = _ids(incoming[1:], name)
        if not old_ids.issubset(new_ids):
            raise ValueError("ID antigo ausente em " + name)
        if name == FILES[0]:
            for line, row in enumerate(incoming[1:], 2):
                _valid_url(row[25].strip(), name + " linha " + str(line), allow_local=True)
    else:
        if len(incoming) < len(current):
            raise ValueError("Instituição antiga ausente no CSV geográfico")
        for line, row in enumerate(incoming, 1):
            if not re.fullmatch(r"[A-Z]{2}", row[2].strip()):
                raise ValueError("UF inválida no CSV geográfico linha " + str(line))
            for index, limit in ((3, 90), (4, 180)):
                try:
                    number = float(row[index])
                except ValueError as exc:
                    raise ValueError("Coordenada inválida no CSV geográfico linha " + str(line)) from exc
                if not math.isfinite(number) or abs(number) > limit:
                    raise ValueError("Coordenada inválida no CSV geográfico linha " + str(line))
            for index in (0, 1, 2, 6):
                if "<" in row[index] or ">" in row[index]:
                    raise ValueError("HTML inseguro no CSV geográfico linha " + str(line))
            _valid_url(row[5].strip(), name + " linha " + str(line))
    return incoming


def _write_csv(rows):
    output = io.StringIO(newline="")
    csv.writer(output, delimiter=";", lineterminator="\n").writerows(rows)
    return output.getvalue().encode("utf-8")


def sync_from_texts(exports, data_dir, dry_run=False):
    """Valida o conjunto inteiro antes de substituir qualquer arquivo."""
    data_dir = Path(data_dir)
    parsed, current = {}, {}
    for name, width in zip(FILES, WIDTHS):
        if name not in exports:
            raise ValueError("Fonte ausente: " + name)
        with (data_dir / name).open(encoding="utf-8-sig", newline="") as handle:
            current[name] = list(csv.reader(handle, delimiter=";"))
        parsed[name] = _validate(name, _read_csv(exports[name], ","), current[name], width)
    instrument_ids = _ids(parsed[FILES[0]][1:], FILES[0])
    aditivo_counts = Counter(row[1].strip() for row in parsed[FILES[1]][1:])
    for row in parsed[FILES[1]][1:]:
        if row[1].strip() not in instrument_ids:
            raise ValueError("Aditivo sem instrumento correspondente: " + row[0])
    for row in parsed[FILES[0]][1:]:
        count = aditivo_counts[row[0].strip()]
        declared = row[11].strip()
        if declared and (not declared.isdigit() or int(declared) != count):
            raise ValueError("Número de aditivos inconsistente no instrumento " + row[0])
        if (row[10].strip().upper() == "SIM") != (count > 0):
            raise ValueError("Indicador de aditivo inconsistente no instrumento " + row[0])
        if count and not declared:
            raise ValueError("Número de aditivos ausente no instrumento " + row[0])

    changed = [name for name in FILES if parsed[name] != current[name]]
    if dry_run or not changed:
        return changed
    backup = data_dir.parent / "_backups" / ("sync-sheets-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    backup.mkdir(parents=True, exist_ok=False)
    for name in changed:
        shutil.copy2(data_dir / name, backup / name)
    staged = {}
    try:
        for name in changed:
            with tempfile.NamedTemporaryFile(dir=data_dir, prefix=".sync-", delete=False) as temp:
                temp.write(_write_csv(parsed[name]))
                staged[name] = Path(temp.name)
        for name in changed:
            os.replace(staged[name], data_dir / name)
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)
    return changed


def _download(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "docs.google.com" or "/spreadsheets/" not in parts.path:
        raise ValueError("URL de fonte Google Sheets inválida")
    request = urllib.request.Request(url, headers={"User-Agent": "FAROL-Sheets-Sync/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="valida sem alterar arquivos")
    args = parser.parse_args()
    urls = {
        FILES[0]: os.environ.get("FAROL_INSTRUMENTOS_CSV_URL", ""),
        FILES[1]: os.environ.get("FAROL_ADITIVOS_CSV_URL", ""),
        FILES[2]: os.environ.get("FAROL_INSTITUICOES_CSV_URL", ""),
    }
    if not all(urls.values()):
        parser.error("Defina as três URLs FAROL_*_CSV_URL")
    exports = {name: _download(url) for name, url in urls.items()}
    changed = sync_from_texts(exports, ROOT / "data", dry_run=args.dry_run)
    print("Validação concluída. Arquivos diferentes: " + (", ".join(changed) if changed else "nenhum"))


if __name__ == "__main__":
    main()
