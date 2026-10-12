from math import sqrt
from fastapi.testclient import TestClient


def _dataset(client: TestClient):
    protein=client.post("/api/v1/nmr/proteins",json={"name":"ANC2","sequence":"M"}).json()
    residue=client.post("/api/v1/nmr/residues",json={"protein_id":protein["id"],"sequence_number":1,"residue_name":"MET","one_letter_code":"M"}).json()
    sample=client.post("/api/v1/nmr/samples",json={"name":"ANC2","protein_ids":[protein["id"]]}).json()
    spectra=[]
    for name in ("reference","bound"):
        spectra.append(client.post("/api/v1/nmr/spectra",json={"name":name,"sample_id":sample["id"],"nuclei":["1H","15N"]}).json())
    for spectrum,h,n in ((spectra[0],8.0,120.0),(spectra[1],8.1,121.0)):
        for atom,nucleus,value in (("H","1H",h),("N","15N",n)):
            assert client.post("/api/v1/nmr/chemical-shifts",json={"spectrum_id":spectrum["id"],"residue_id":residue["id"],"atom_name":atom,"nucleus":nucleus,"value_ppm":value}).status_code==201
    return spectra,residue


def test_compare_spectra_returns_observed_deltas(client: TestClient) -> None:
    spectra,_=_dataset(client)
    response=client.post("/api/v1/nmr/analyses/compare-spectra",json={"reference_spectrum_id":spectra[0]["id"],"comparison_spectrum_id":spectra[1]["id"]})
    assert response.status_code==200
    data=response.json(); assert data["matched_shift_count"]==2; assert data["reference_only_count"]==0
    values={item["atom_name"]:item["delta_ppm"] for item in data["deltas"]}
    assert abs(values["H"]-0.1)<1e-12 and values["N"]==1.0


def test_csp_reports_formula_weights_and_exact_components(client: TestClient) -> None:
    spectra,_=_dataset(client)
    response=client.post("/api/v1/nmr/analyses/chemical-shift-perturbation",json={"reference_spectrum_id":spectra[0]["id"],"comparison_spectrum_id":spectra[1]["id"]})
    assert response.status_code==200
    data=response.json(); assert data["nucleus_weights"]=={"1H":1.0,"15N":0.154}; assert data["residue_count"]==1
    assert abs(data["residues"][0]["perturbation_ppm"]-sqrt(0.1**2+(0.154*1.0)**2))<1e-12
    assert data["formula"]=="sqrt(sum((nucleus_weight * delta_ppm)^2))"


def test_analysis_rejects_same_spectrum_and_nonpositive_weights(client: TestClient) -> None:
    spectra,_=_dataset(client); spectrum_id=spectra[0]["id"]
    assert client.post("/api/v1/nmr/analyses/compare-spectra",json={"reference_spectrum_id":spectrum_id,"comparison_spectrum_id":spectrum_id}).status_code==422
    assert client.post("/api/v1/nmr/analyses/chemical-shift-perturbation",json={"reference_spectrum_id":spectra[0]["id"],"comparison_spectrum_id":spectra[1]["id"],"nucleus_weights":{"1H":0}}).status_code==422
