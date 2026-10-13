"""Deterministic, evidence-only summaries for agent tool results."""
from __future__ import annotations

from typing import Any


def _items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return [data] if isinstance(data, dict) else []


def _value(value: Any, fallback: str = "not recorded") -> str:
    if value is None or value == "" or value == []:
        return fallback
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _heading(noun: str, count: int) -> str:
    return f"I found {count} {noun if count == 1 else noun + 's'}:"


def _format_records(tool_name: str, data: Any) -> str:
    records = _items(data)
    if not records:
        return "No matching records were found."

    if tool_name in {"get_project", "list_projects"}:
        lines = [f"- {item.get('title', 'Untitled project')} ({_value(item.get('code'))}) — {_value(item.get('status'))}; {item.get('experiment_count', 0)} experiments, {item.get('workflow_count', 0)} workflows" for item in records]
        return "\n".join([_heading("project", len(records)), *lines])
    if tool_name in {"get_workflow", "list_workflows"}:
        lines = [f"- {item.get('title', 'Untitled workflow')} — {_value(item.get('library_state'))}; version {item.get('version', '?')}, {len(item.get('steps') or [])} steps" for item in records]
        return "\n".join([_heading("workflow", len(records)), *lines])
    if tool_name in {"get_experiment", "list_experiments", "search_experiment_notes"}:
        lines = [f"- {item.get('title', 'Untitled experiment')} — {_value(item.get('experiment_date'))}; {_value(item.get('status'))}" + (f". Notes: {item['notes']}" if item.get("notes") else "") for item in records]
        return "\n".join([_heading("experiment", len(records)), *lines])
    if tool_name == "get_experiment_run_step":
        item = records[0]
        return f"Experiment step: {item.get('label', 'Untitled step')} — {_value(item.get('status'))}; order {item.get('order_index', '?')}."
    if tool_name in {"get_sample", "list_samples"}:
        lines = []
        for item in records:
            concentration = ""
            if item.get("concentration_value") is not None:
                concentration = f"; {item['concentration_value']} {_value(item.get('concentration_unit'), '')}".rstrip()
            ph = f"; pH {item['ph']}" if item.get("ph") is not None else ""
            lines.append(f"- {item.get('name', 'Unnamed sample')} — {_value(item.get('sample_type'))}{concentration}{ph}; {_value(item.get('status'))}")
        return "\n".join([_heading("sample", len(records)), *lines])
    if tool_name in {"get_protein", "list_proteins"}:
        lines = [f"- {item.get('name', 'Unnamed protein')}" + (f" ({item['construct_name']})" if item.get("construct_name") else "") + f" — {item.get('residue_count', 0)} stored residues; labels: {_value(item.get('isotope_labels'), 'none')}" for item in records]
        return "\n".join([_heading("protein", len(records)), *lines])
    if tool_name in {"get_ligand", "list_ligands"}:
        lines = [f"- {item.get('name', 'Unnamed ligand')} — identifier: {_value(item.get('identifier'))}; formula: {_value(item.get('molecular_formula'))}" for item in records]
        return "\n".join([_heading("ligand", len(records)), *lines])
    if tool_name in {"get_spectrum", "list_spectra"}:
        lines = [f"- {item.get('name', 'Unnamed spectrum')} — {_value(item.get('experiment_type'))}; nuclei: {_value(item.get('nuclei'))}; {item.get('peak_count', 0)} peaks" for item in records]
        return "\n".join([_heading("spectrum", len(records)), *lines])
    if tool_name in {"get_peak", "list_peaks"}:
        lines = [f"- {item.get('label') or item.get('id', 'Unlabelled peak')} — {_value(item.get('positions_ppm'))} ppm; {item.get('assignment_count', 0)} assignments" for item in records]
        return "\n".join([_heading("peak", len(records)), *lines])
    if tool_name == "get_peak_assignments":
        lines = [f"- Residue {item.get('residue_id', 'unknown')}: {_value(item.get('atom_names'))} — {_value(item.get('status'))}" + (f" ({round(item['confidence'] * 100)}% confidence)" if item.get("confidence") is not None else "") for item in records]
        return "\n".join([_heading("assignment", len(records)), *lines])
    if tool_name == "find_residue":
        lines = [f"- {item.get('one_letter_code', '?')}{item.get('sequence_number', '?')} ({_value(item.get('residue_name'))})" for item in records]
        return "\n".join([_heading("residue", len(records)), *lines])
    if tool_name == "get_residue_shifts":
        lines = [f"- {item.get('atom_name', '?')} ({item.get('nucleus', '?')}): {item.get('value_ppm', '?')} ppm" for item in records]
        return "\n".join([_heading("chemical shift", len(records)), *lines])
    if tool_name == "compare_spectra":
        item = records[0]
        return f"Spectrum comparison: {item.get('matched_shift_count', 0)} matched shifts, {item.get('reference_only_count', 0)} reference-only, and {item.get('comparison_only_count', 0)} comparison-only."
    if tool_name == "calculate_chemical_shift_perturbation":
        item = records[0]
        lines = [f"- {entry.get('residue_name', '?')}{entry.get('sequence_number', '?')}: {entry.get('perturbation_ppm', '?')} ppm" for entry in (item.get("residues") or [])[:20]]
        return "\n".join([f"Chemical-shift perturbation results for {item.get('residue_count', len(lines))} residues:", *lines])
    if tool_name == "list_chat_channels":
        lines = [f"- #{item.get('name', 'unnamed')} — {item.get('message_count', 0)} messages" for item in records]
        return "\n".join([_heading("channel", len(records)), *lines])
    if tool_name == "list_channel_messages":
        lines = [f"- {_value(item.get('author_display_name'), 'Unknown author')}: {item.get('body', '')}" for item in records]
        return "\n".join([_heading("message", len(records)), *lines])

    labels = [item.get("title") or item.get("name") or item.get("label") or item.get("id") for item in records]
    return "Retrieved records:\n" + "\n".join(f"- {_value(label)}" for label in labels)


def format_tool_evidence(results: list[dict[str, Any]]) -> str:
    """Summarize only data present in successful, audited tool results."""
    sections = [_format_records(result.get("tool_name", ""), result.get("data")) for result in results]
    return "\n\n".join(section for section in sections if section)
