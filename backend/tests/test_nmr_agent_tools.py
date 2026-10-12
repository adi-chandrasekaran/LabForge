from fastapi.testclient import TestClient

def invoke(client:TestClient,name:str,args:dict): return client.post(f"/api/v1/agent/tools/{name}/invoke",json={"arguments":args,"confirmed":False})

def _dataset(client:TestClient):
    protein=client.post("/api/v1/nmr/proteins",json={"name":"ANC2","sequence":"M"}).json(); residue=client.post("/api/v1/nmr/residues",json={"protein_id":protein["id"],"sequence_number":1,"residue_name":"MET","one_letter_code":"M"}).json(); sample=client.post("/api/v1/nmr/samples",json={"name":"ANC2 sample","protein_ids":[protein["id"]]}).json()
    spectra=[client.post("/api/v1/nmr/spectra",json={"name":name,"sample_id":sample["id"],"nuclei":["1H","15N"]}).json() for name in ("reference","bound")]
    peaks=[]
    for spectrum,h,n in ((spectra[0],8.0,120.0),(spectra[1],8.1,121.0)):
        peak=client.post("/api/v1/nmr/peaks",json={"spectrum_id":spectrum["id"],"positions_ppm":[h,n]}).json(); peaks.append(peak)
        client.post("/api/v1/nmr/assignments",json={"peak_id":peak["id"],"residue_id":residue["id"],"atom_names":["H","N"]})
        for atom,nucleus,value in (("H","1H",h),("N","15N",n)): client.post("/api/v1/nmr/chemical-shifts",json={"spectrum_id":spectrum["id"],"residue_id":residue["id"],"peak_id":peak["id"],"atom_name":atom,"nucleus":nucleus,"value_ppm":value})
    return protein,residue,sample,spectra,peaks

def test_nmr_entity_tools_return_stored_data(client:TestClient):
    protein,residue,sample,spectra,peaks=_dataset(client)
    assert invoke(client,"get_sample",{"sample_id":sample["id"]}).json()["data"]["protein_ids"]==[protein["id"]]
    assert invoke(client,"find_residue",{"protein_id":protein["id"],"sequence_number":1}).json()["data"][0]["id"]==residue["id"]
    assert len(invoke(client,"get_peak_assignments",{"peak_id":peaks[0]["id"]}).json()["data"])==1
    assert len(invoke(client,"get_residue_shifts",{"residue_id":residue["id"],"spectrum_id":spectra[0]["id"]}).json()["data"])==2

def test_nmr_analysis_tools_return_service_results(client:TestClient):
    _,_,_,spectra,_=_dataset(client); args={"reference_spectrum_id":spectra[0]["id"],"comparison_spectrum_id":spectra[1]["id"]}
    comparison=invoke(client,"compare_spectra",args).json(); assert comparison["ok"] is True and comparison["data"]["matched_shift_count"]==2
    csp=invoke(client,"calculate_chemical_shift_perturbation",args).json(); assert csp["ok"] is True and csp["data"]["residue_count"]==1 and csp["data"]["formula"]
