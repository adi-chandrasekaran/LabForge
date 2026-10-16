from backend.app.agent_presenter import format_tool_evidence


def test_formats_projects_without_internal_record_noise() -> None:
    answer = format_tool_evidence([{
        "tool_name": "list_projects",
        "data": [{
            "id": "project-anc2",
            "title": "ANC2 Protein Purification",
            "code": "ANC2-PURIF-2026",
            "status": "active",
            "experiment_count": 17,
            "workflow_count": 2,
            "owner_id": "user-dev-chen",
            "members": [{"email": "chen@nmr-lab.local"}],
        }],
    }])

    assert "I found 1 project:" in answer
    assert "ANC2 Protein Purification (ANC2-PURIF-2026)" in answer
    assert "17 experiments, 2 workflows" in answer
    assert "owner_id" not in answer
    assert "chen@nmr-lab.local" not in answer


def test_formats_nmr_records_with_scientific_units() -> None:
    answer = format_tool_evidence([
        {"tool_name": "list_spectra", "data": [{"name": "ANC2 reference", "experiment_type": "HSQC", "nuclei": ["1H", "15N"], "peak_count": 42}]},
        {"tool_name": "get_residue_shifts", "data": [{"atom_name": "H", "nucleus": "1H", "value_ppm": 8.12}]},
    ])

    assert "ANC2 reference — HSQC; nuclei: 1H, 15N; 42 peaks" in answer
    assert "H (1H): 8.12 ppm" in answer


def test_formats_analysis_summaries_and_empty_results() -> None:
    comparison = format_tool_evidence([{
        "tool_name": "compare_spectra",
        "data": {"matched_shift_count": 6, "reference_only_count": 1, "comparison_only_count": 2},
    }])
    empty = format_tool_evidence([{"tool_name": "find_residue", "data": []}])

    assert comparison == "Spectrum comparison: 6 matched shifts, 1 reference-only, and 2 comparison-only."
    assert empty == "No matching records were found."


def test_omits_empty_auxiliary_results_when_evidence_exists() -> None:
    answer = format_tool_evidence([
        {"tool_name": "list_spectra", "data": [{"name": "ANC2 reference", "experiment_type": "HSQC", "nuclei": ["1H", "15N"], "peak_count": 1}]},
        {"tool_name": "list_samples", "data": []},
    ])

    assert "ANC2 reference" in answer
    assert "No matching records" not in answer
