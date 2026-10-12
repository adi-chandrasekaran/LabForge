from fastapi.testclient import TestClient


def _foundation(client: TestClient) -> tuple[str, str]:
    protein = client.post("/api/v1/nmr/proteins", json={"name":"ANC2","sequence":"M"}).json()
    residue = client.post("/api/v1/nmr/residues", json={"protein_id":protein["id"],"sequence_number":1,"residue_name":"MET","one_letter_code":"M"}).json()
    sample = client.post("/api/v1/nmr/samples", json={"name":"ANC2 HSQC","protein_ids":[protein["id"]]}).json()
    return sample["id"], residue["id"]


def test_spectrum_peak_assignment_and_shift_flow(client: TestClient) -> None:
    sample_id,residue_id=_foundation(client)
    spectrum=client.post("/api/v1/nmr/spectra",json={"name":"ANC2 reference","sample_id":sample_id,"experiment_type":"1H-15N HSQC","nuclei":["1H","15N"],"spectrometer_frequency_mhz":600}).json()
    peak=client.post("/api/v1/nmr/peaks",json={"spectrum_id":spectrum["id"],"label":"M1","positions_ppm":[8.12,121.4],"intensity":1500}).json()
    assignment=client.post("/api/v1/nmr/assignments",json={"peak_id":peak["id"],"residue_id":residue_id,"atom_names":["H","N"],"confidence":0.95,"status":"confirmed"})
    assert assignment.status_code==201
    shift_h=client.post("/api/v1/nmr/chemical-shifts",json={"spectrum_id":spectrum["id"],"residue_id":residue_id,"peak_id":peak["id"],"atom_name":"H","nucleus":"1H","value_ppm":8.12})
    shift_n=client.post("/api/v1/nmr/chemical-shifts",json={"spectrum_id":spectrum["id"],"residue_id":residue_id,"peak_id":peak["id"],"atom_name":"N","nucleus":"15N","value_ppm":121.4})
    assert shift_h.status_code==201 and shift_n.status_code==201
    assert client.get(f'/api/v1/nmr/spectra/{spectrum["id"]}').json()["peak_count"]==1
    assert client.get(f'/api/v1/nmr/peaks/{peak["id"]}').json()["assignment_count"]==1
    assert len(client.get(f'/api/v1/nmr/chemical-shifts?residue_id={residue_id}').json())==2


def test_peak_dimensions_and_shift_uniqueness_are_validated(client: TestClient) -> None:
    sample_id,residue_id=_foundation(client)
    spectrum=client.post("/api/v1/nmr/spectra",json={"name":"2D","sample_id":sample_id,"nuclei":["1H","15N"]}).json()
    assert client.post("/api/v1/nmr/peaks",json={"spectrum_id":spectrum["id"],"positions_ppm":[8.0]}).status_code==422
    peak=client.post("/api/v1/nmr/peaks",json={"spectrum_id":spectrum["id"],"positions_ppm":[8.0,120.0]}).json()
    shift={"spectrum_id":spectrum["id"],"residue_id":residue_id,"peak_id":peak["id"],"atom_name":"H","nucleus":"1H","value_ppm":8.0}
    assert client.post("/api/v1/nmr/chemical-shifts",json=shift).status_code==201
    assert client.post("/api/v1/nmr/chemical-shifts",json=shift).status_code==409


def test_spectrum_delete_cascades_spectral_records(client: TestClient) -> None:
    sample_id,residue_id=_foundation(client)
    spectrum=client.post("/api/v1/nmr/spectra",json={"name":"Delete","sample_id":sample_id,"nuclei":["1H"]}).json()
    peak=client.post("/api/v1/nmr/peaks",json={"spectrum_id":spectrum["id"],"positions_ppm":[8.0]}).json()
    client.post("/api/v1/nmr/assignments",json={"peak_id":peak["id"],"residue_id":residue_id,"atom_names":["H"]})
    client.post("/api/v1/nmr/chemical-shifts",json={"spectrum_id":spectrum["id"],"residue_id":residue_id,"peak_id":peak["id"],"atom_name":"H","nucleus":"1H","value_ppm":8.0})
    assert client.delete(f'/api/v1/nmr/spectra/{spectrum["id"]}').status_code==204
    assert client.get(f'/api/v1/nmr/peaks/{peak["id"]}').status_code==404
