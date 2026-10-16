from fastapi.testclient import TestClient


def _upload(client: TestClient, entity_type: str, csv_text: str, *, dry_run: bool):
    return client.post(
        f"/api/v1/nmr/imports/{entity_type}?dry_run={'true' if dry_run else 'false'}",
        files={"file": (f"{entity_type}.csv", csv_text.encode(), "text/csv")},
    )


def _foundation(client: TestClient) -> tuple[str, str, str]:
    protein = client.post("/api/v1/nmr/proteins", json={"name": "ANC2", "sequence": "MA"}).json()
    sample = client.post("/api/v1/nmr/samples", json={"name": "ANC2 sample", "protein_ids": [protein["id"]]}).json()
    spectrum = client.post(
        "/api/v1/nmr/spectra",
        json={"name": "ANC2 HSQC", "sample_id": sample["id"], "nuclei": ["1H", "15N"]},
    ).json()
    return protein["id"], sample["id"], spectrum["id"]


def test_preview_then_import_complete_nmr_dataset(client: TestClient) -> None:
    protein_id, _, spectrum_id = _foundation(client)
    residues = (
        "protein_id,sequence_number,residue_name,one_letter_code\n"
        f"{protein_id},1,MET,M\n"
        f"{protein_id},2,ALA,A\n"
    )
    preview = _upload(client, "residues", residues, dry_run=True)
    assert preview.status_code == 200
    assert preview.json() | {"imported_ids": []} == {
        "entity_type": "residues",
        "dry_run": True,
        "total_rows": 2,
        "valid_rows": 2,
        "imported_count": 0,
        "imported_ids": [],
        "errors": [],
    }
    assert client.get(f"/api/v1/nmr/residues?protein_id={protein_id}").json() == []

    imported = _upload(client, "residues", residues, dry_run=False)
    assert imported.status_code == 200
    assert imported.json()["imported_count"] == 2
    residue_ids = imported.json()["imported_ids"]

    peaks = (
        "spectrum_id,label,position_1_ppm,position_2_ppm,intensity\n"
        f"{spectrum_id},M1,8.12,121.4,1500\n"
        f"{spectrum_id},A2,8.30,124.2,1200\n"
    )
    peak_result = _upload(client, "peaks", peaks, dry_run=False).json()
    assert peak_result["imported_count"] == 2

    assignments = (
        "peak_id,residue_id,atom_names,confidence,status\n"
        f'{peak_result["imported_ids"][0]},{residue_ids[0]},H;N,0.98,confirmed\n'
    )
    assert _upload(client, "assignments", assignments, dry_run=False).json()["imported_count"] == 1

    shifts = (
        "spectrum_id,residue_id,peak_id,atom_name,nucleus,value_ppm,uncertainty_ppm\n"
        f'{spectrum_id},{residue_ids[0]},{peak_result["imported_ids"][0]},H,1H,8.12,0.01\n'
        f'{spectrum_id},{residue_ids[0]},{peak_result["imported_ids"][0]},N,15N,121.4,0.05\n'
    )
    shift_result = _upload(client, "chemical_shifts", shifts, dry_run=False).json()
    assert shift_result["imported_count"] == 2
    assert len(client.get(f"/api/v1/nmr/chemical-shifts?spectrum_id={spectrum_id}").json()) == 2


def test_import_reports_rows_and_writes_nothing_when_validation_fails(client: TestClient) -> None:
    protein_id, _, spectrum_id = _foundation(client)
    invalid_peaks = (
        "spectrum_id,label,position_1_ppm,position_2_ppm\n"
        f"{spectrum_id},valid,8.12,121.4\n"
        f"{spectrum_id},invalid,not-a-number,124.2\n"
    )
    result = _upload(client, "peaks", invalid_peaks, dry_run=False)
    assert result.status_code == 200
    assert result.json()["imported_count"] == 0
    assert result.json()["errors"][0]["row"] == 3
    assert client.get(f"/api/v1/nmr/peaks?spectrum_id={spectrum_id}").json() == []

    missing_parent = (
        "protein_id,sequence_number,residue_name,one_letter_code\n"
        "missing-protein,1,MET,M\n"
    )
    missing = _upload(client, "residues", missing_parent, dry_run=True).json()
    assert missing["errors"] == [{"row": 2, "field": None, "message": "Protein not found"}]
    assert client.get(f"/api/v1/nmr/residues?protein_id={protein_id}").json() == []


def test_import_preserves_source_row_numbers_after_an_earlier_parse_error(client: TestClient) -> None:
    malformed_then_missing_parent = (
        "protein_id,sequence_number,residue_name,one_letter_code\n"
        "missing-protein,not-a-number,MET,M\n"
        "missing-protein,2,ALA,A\n"
    )

    result = _upload(client, "residues", malformed_then_missing_parent, dry_run=True)

    assert result.status_code == 200
    assert result.json()["valid_rows"] == 0
    assert [error["row"] for error in result.json()["errors"]] == [2, 3]
    assert result.json()["errors"][1]["message"] == "Protein not found"


def test_import_rejects_unsupported_empty_and_oversized_files(client: TestClient) -> None:
    formats = client.get("/api/v1/nmr/imports")
    assert formats.status_code == 200
    assert {item["entity_type"] for item in formats.json()} == {
        "residues", "peaks", "assignments", "chemical_shifts"
    }
    assert _upload(client, "unknown", "value\n1\n", dry_run=True).status_code == 404
    missing_header = _upload(client, "peaks", "spectrum_id,label\nvalue,name\n", dry_run=True)
    assert missing_header.status_code == 422
    assert "position_1_ppm" in missing_header.json()["detail"]
    assert _upload(client, "peaks", "spectrum_id,position_1_ppm\n", dry_run=True).status_code == 422
    oversized = b"x" * 1_000_001
    response = client.post(
        "/api/v1/nmr/imports/peaks",
        files={"file": ("large.csv", oversized, "text/csv")},
    )
    assert response.status_code == 413
