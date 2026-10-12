from fastapi.testclient import TestClient
from backend.app import database
from backend.app.models import Protein, User


def test_nmr_domain_crud_and_relationships(client: TestClient) -> None:
    protein = client.post("/api/v1/nmr/proteins", json={
        "name": "ANC2", "construct_name": "ANC2 1-120", "sequence": "MAGS", "isotope_labels": ["15N"],
    })
    assert protein.status_code == 201
    protein_id = protein.json()["id"]

    ligand = client.post("/api/v1/nmr/ligands", json={
        "name": "ATP", "identifier": "ATP", "molecular_formula": "C10H16N5O13P3",
    })
    assert ligand.status_code == 201
    ligand_id = ligand.json()["id"]

    residue = client.post("/api/v1/nmr/residues", json={
        "protein_id": protein_id, "sequence_number": 1, "residue_name": "MET", "one_letter_code": "M",
    })
    assert residue.status_code == 201
    assert client.get(f"/api/v1/nmr/proteins/{protein_id}").json()["residue_count"] == 1

    sample = client.post("/api/v1/nmr/samples", json={
        "name": "ANC2 + ATP", "sample_type": "protein_ligand", "concentration_value": 0.2,
        "concentration_unit": "mM", "buffer": "20 mM phosphate", "ph": 6.8,
        "protein_ids": [protein_id], "ligand_ids": [ligand_id],
    })
    assert sample.status_code == 201
    assert sample.json()["protein_ids"] == [protein_id]
    assert sample.json()["ligand_ids"] == [ligand_id]

    sample_id = sample.json()["id"]
    updated = client.put(f"/api/v1/nmr/samples/{sample_id}", json={
        "name": "ANC2 titration", "protein_ids": [protein_id], "ligand_ids": [ligand_id], "ph": 7.0,
    })
    assert updated.status_code == 200
    assert updated.json()["ph"] == 7.0
    assert client.delete(f"/api/v1/nmr/samples/{sample_id}").status_code == 204
    assert client.get(f"/api/v1/nmr/samples/{sample_id}").status_code == 404


def test_residue_positions_are_unique_per_protein(client: TestClient) -> None:
    protein_id = client.post("/api/v1/nmr/proteins", json={"name": "Unique positions"}).json()["id"]
    payload = {"protein_id": protein_id, "sequence_number": 42, "residue_name": "GLY", "one_letter_code": "G"}
    assert client.post("/api/v1/nmr/residues", json=payload).status_code == 201
    response = client.post("/api/v1/nmr/residues", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Residue position already exists for this protein"


def test_sample_rejects_unknown_components_and_invalid_scientific_values(client: TestClient) -> None:
    assert client.post("/api/v1/nmr/samples", json={"name": "Bad", "protein_ids": ["missing"]}).status_code == 404
    assert client.post("/api/v1/nmr/samples", json={"name": "Bad pH", "ph": 15}).status_code == 422
    assert client.post("/api/v1/nmr/proteins", json={"name": "Bad mass", "molecular_weight_da": -1}).status_code == 422


def test_cross_lab_protein_is_not_visible(client: TestClient) -> None:
    db = database.SessionLocal()
    try:
        db.add(User(id="other-user", email="other@nmr.local", display_name="Other", role="student", lab_id="other-lab"))
        db.add(Protein(id="protein-other", lab_id="other-lab", owner_id="other-user", name="Private", construct_name="", sequence="", isotope_labels=[], notes=""))
        db.commit()
    finally:
        db.close()
    assert client.get("/api/v1/nmr/proteins/protein-other").status_code == 404
    assert all(item["id"] != "protein-other" for item in client.get("/api/v1/nmr/proteins").json())
