import csv
import io
import tempfile
import unittest
from pathlib import Path

from _migracao.sync_sheets_csv import sync_from_texts


ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "tbl_instrumentos.csv",
    "tbl_aditivos.csv",
    "tbl_instituicoes_geo.csv",
)


def rows(path, delimiter=";"):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle, delimiter=delimiter))


def encoded(data, delimiter=","):
    output = io.StringIO(newline="")
    csv.writer(output, delimiter=delimiter, lineterminator="\r\n").writerows(data)
    return output.getvalue()


class SyncSheetsCsvTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_dir = Path(self.tmp.name) / "data"
        self.data_dir.mkdir()
        self.baseline = {}
        for name in FILES:
            source = ROOT / "data" / name
            current = rows(source)
            self.baseline[name] = current
            with (self.data_dir / name).open("w", encoding="utf-8", newline="") as handle:
                csv.writer(handle, delimiter=";", lineterminator="\n").writerows(self.baseline[name])

    def exports(self):
        return {name: encoded(data) for name, data in self.baseline.items()}

    def test_google_csv_becomes_semicolon_csv_without_losing_quoted_text(self):
        exports = self.exports()
        instruments = [row[:] for row in self.baseline[FILES[0]]]
        instruments[1][18] = "Produto A; Produto B, em Manaus"
        exports[FILES[0]] = "\ufeff" + encoded(instruments)

        changed = sync_from_texts(exports, self.data_dir)

        self.assertEqual(changed, [FILES[0]])
        self.assertEqual(rows(self.data_dir / FILES[0])[1][18], "Produto A; Produto B, em Manaus")
        self.assertEqual(rows(self.data_dir / FILES[0])[0], self.baseline[FILES[0]][0])

    def test_invalid_geo_prevents_any_of_three_files_from_changing(self):
        exports = self.exports()
        instruments = [row[:] for row in self.baseline[FILES[0]]]
        instruments[1][18] = "alterado"
        exports[FILES[0]] = encoded(instruments)
        exports[FILES[2]] = encoded([["nome", "cidade", "UF"]])
        before = {name: (self.data_dir / name).read_bytes() for name in FILES}

        with self.assertRaises(ValueError):
            sync_from_texts(exports, self.data_dir)

        self.assertEqual(before, {name: (self.data_dir / name).read_bytes() for name in FILES})

    def test_geo_header_from_query_is_removed_before_publication(self):
        exports = self.exports()
        header = ["nome", "cidade", "uf", "lat", "lon", "url", "sigla"]
        exports[FILES[2]] = encoded([header] + self.baseline[FILES[2]])

        changed = sync_from_texts(exports, self.data_dir)

        self.assertEqual(changed, [])
        self.assertEqual(rows(self.data_dir / FILES[2]), self.baseline[FILES[2]])

    def test_missing_instrument_id_is_rejected_instead_of_deleting_it(self):
        exports = self.exports()
        exports[FILES[0]] = encoded([self.baseline[FILES[0]][0]])

        with self.assertRaisesRegex(ValueError, "ID.*ausente|vazio"):
            sync_from_texts(exports, self.data_dir)

        self.assertEqual(rows(self.data_dir / FILES[0]), self.baseline[FILES[0]])

    def test_invalid_date_and_unsafe_links_are_rejected(self):
        for field, value in ((8, "31/02/2026"), (25, "javascript:alert(1)")):
            with self.subTest(field=field):
                exports = self.exports()
                instruments = [row[:] for row in self.baseline[FILES[0]]]
                instruments[1][field] = value
                exports[FILES[0]] = encoded(instruments)
                with self.assertRaises(ValueError):
                    sync_from_texts(exports, self.data_dir)

    def test_unsafe_geo_html_is_rejected(self):
        exports = self.exports()
        geo = [row[:] for row in self.baseline[FILES[2]]]
        geo[0][0] = "<img src=x>"
        exports[FILES[2]] = encoded(geo)

        with self.assertRaises(ValueError):
            sync_from_texts(exports, self.data_dir)

    def test_duplicate_instrument_and_orphan_aditivo_are_rejected(self):
        for kind in ("duplicate", "orphan"):
            with self.subTest(kind=kind):
                exports = self.exports()
                if kind == "duplicate":
                    instruments = [row[:] for row in self.baseline[FILES[0]]]
                    instruments.append(instruments[1][:])
                    exports[FILES[0]] = encoded(instruments)
                else:
                    aditivos = [row[:] for row in self.baseline[FILES[1]]]
                    aditivos[1][1] = "99999"
                    exports[FILES[1]] = encoded(aditivos)
                with self.assertRaises(ValueError):
                    sync_from_texts(exports, self.data_dir)

    def test_invalid_geo_coordinate_and_quoted_link_are_rejected(self):
        for field, value in ((3, "NaN"), (5, "https://site.org/' onclick='x")):
            with self.subTest(field=field):
                exports = self.exports()
                geo = [row[:] for row in self.baseline[FILES[2]]]
                geo[0][field] = value
                exports[FILES[2]] = encoded(geo)
                with self.assertRaises(ValueError):
                    sync_from_texts(exports, self.data_dir)

    def test_aditivo_count_must_match_instrument_flag(self):
        exports = self.exports()
        instruments = [row[:] for row in self.baseline[FILES[0]]]
        instruments[1][10] = "SIM"
        instruments[1][11] = "1"
        exports[FILES[0]] = encoded(instruments)

        with self.assertRaisesRegex(ValueError, "aditivo"):
            sync_from_texts(exports, self.data_dir)


if __name__ == "__main__":
    unittest.main()
