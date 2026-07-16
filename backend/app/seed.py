from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .models import ChatChannel, ChatMessage, Project, User, Workflow, WorkflowStep


def _io(name: str, item_type: str, value: Optional[str] = None, note: Optional[str] = None) -> dict:
    item = {"name": name, "type": item_type}
    if value is not None:
        item["value"] = value
    if note is not None:
        item["note"] = note
    return item


def _param(label: str, value: str) -> dict:
    return {"label": label, "value": value}


ANC2_BATCH_1_STEPS = [
    {
        "id": "b1-01",
        "order_index": 1,
        "label": "Cell Lysis",
        "status_template": "complete",
        "duration": "2 hr",
        "procedure_markdown": "Lyse the cell pellet on ice with native lysis buffer, lysozyme, and protease inhibitor, then sonicate and clarify.",
        "inputs": [
            _io("E. coli pellet (His-SUMO-ANC2)", "sample", "~8 g"),
            _io("Lysis Buffer", "buffer", "40 mL", "50 mM Tris pH 8, 300 mM NaCl, 10 mM imidazole"),
            _io("Lysozyme", "reagent", "1 mg/mL"),
            _io("cOmplete Protease Inhibitor", "reagent", "1 tablet/50 mL"),
            _io("Sonicator (Branson 450D)", "equipment"),
        ],
        "parameters": [
            _param("Sonication", "6x30s on/60s off, 40% amplitude"),
            _param("Temperature", "4 C (ice bath)"),
            _param("Centrifugation", "15,000 x g, 30 min, 4 C"),
        ],
        "outputs": [
            _io("Clarified lysate (Sup 1)", "sample", None, "Proceed to Ni-NTA"),
            _io("Cell debris pellet", "waste"),
        ],
        "notes": "Keep on ice throughout. Verify lysis by OD600 drop.",
    },
    {
        "id": "b1-02",
        "order_index": 2,
        "label": "Supernatant (Sup 1)",
        "sublabel": "Centrifugation",
        "status_template": "complete",
        "duration": "45 min",
        "procedure_markdown": "Clarify the crude lysate by centrifugation and retain the soluble supernatant.",
        "inputs": [
            _io("Crude lysate", "sample"),
            _io("Beckman Avanti J-26S", "equipment"),
        ],
        "parameters": [
            _param("Speed", "15,000 x g"),
            _param("Duration", "30 min"),
            _param("Temp", "4 C"),
        ],
        "outputs": [
            _io("Sup 1 (clarified)", "sample"),
            _io("Pellet", "waste", None, "Save for troubleshooting"),
        ],
        "notes": "",
    },
    {
        "id": "b1-03",
        "order_index": 3,
        "label": "Ni-NTA Affinity Column",
        "sublabel": "Protein binds Ni resin",
        "status_template": "complete",
        "duration": "3 hr",
        "procedure_markdown": "Equilibrate Ni-NTA, load Sup 1, wash with low imidazole, and monitor A280.",
        "inputs": [
            _io("Sup 1", "sample"),
            _io("Ni-NTA Agarose", "reagent", "5 mL bed"),
            _io("Equilibration Buffer", "buffer", "25 mL", "50 mM Tris pH 8, 300 mM NaCl, 10 mM imidazole"),
            _io("Wash Buffer", "buffer", "50 mL", "25 mM imidazole"),
            _io("AKTA Pure FPLC", "equipment"),
        ],
        "parameters": [
            _param("Flow rate", "1 mL/min"),
            _param("Wash", "5 CV at 25 mM imidazole"),
            _param("Monitor", "A280"),
        ],
        "outputs": [
            _io("Column-bound His-SUMO-ANC2", "sample"),
            _io("Flow-through", "waste"),
        ],
        "notes": "",
    },
    {
        "id": "b1-04",
        "order_index": 4,
        "label": "Elution",
        "sublabel": "Imidazole Buffer",
        "status_template": "complete",
        "duration": "1 hr",
        "procedure_markdown": "Elute the bound fusion protein with 250 mM imidazole and pool A280-positive fractions.",
        "inputs": [
            _io("Bound protein on Ni-NTA", "sample"),
            _io("Elution Buffer", "buffer", "15 mL", "250 mM imidazole"),
        ],
        "parameters": [
            _param("Imidazole", "250 mM"),
            _param("Mode", "Step elution"),
            _param("Fraction size", "2 mL"),
        ],
        "outputs": [
            _io("His-SUMO-ANC2 eluate", "sample", None, "Pool A280+ fractions"),
        ],
        "notes": "",
    },
    {
        "id": "b1-05",
        "order_index": 5,
        "label": "Dialysis",
        "sublabel": "Remove Imidazole",
        "status_template": "running",
        "duration": "Overnight",
        "procedure_markdown": "Dialyze pooled eluate into cleavage-compatible buffer to remove imidazole before ULP1 cleavage.",
        "inputs": [
            _io("Pooled eluate", "sample"),
            _io("Dialysis Buffer", "buffer", "2x2 L", "50 mM Tris pH 8, 150 mM NaCl, 1 mM DTT"),
            _io("SnakeSkin Tubing MWCO 10 kDa", "equipment"),
        ],
        "parameters": [
            _param("Temp", "4 C"),
            _param("Duration", "Overnight"),
            _param("Buffer changes", "2x2 L"),
        ],
        "outputs": [
            _io("Imidazole-free His-SUMO-ANC2", "sample"),
        ],
        "notes": "Confirm imidazole removal before cleavage step.",
    },
    {
        "id": "b1-06",
        "order_index": 6,
        "label": "SUMO Cleavage",
        "sublabel": "Remove His-SUMO Tag",
        "status_template": "pending",
        "duration": "Overnight",
        "procedure_markdown": "Incubate dialyzed fusion protein with ULP1 to cleave the His-SUMO tag.",
        "inputs": [
            _io("Dialyzed His-SUMO-ANC2", "sample"),
            _io("ULP1 SUMO Protease", "reagent", "1:100 w/w"),
        ],
        "parameters": [
            _param("Ratio", "1:100 (protease:protein)"),
            _param("Temp", "4 C"),
            _param("Duration", "16 hr"),
        ],
        "outputs": [
            _io("Cleaved ANC2 (tag-free)", "sample"),
            _io("Free His-SUMO tag", "sample"),
        ],
        "notes": "Verify cleavage by SDS-PAGE before next step.",
    },
    {
        "id": "b1-07",
        "order_index": 7,
        "label": "Reverse Ni-NTA Column",
        "sublabel": "Expected purification",
        "status_template": "pending",
        "duration": "2 hr",
        "procedure_markdown": "Use reverse Ni-NTA to retain His-tagged components and collect tag-free ANC2 in the flow-through.",
        "inputs": [
            _io("Cleavage reaction mix", "sample"),
            _io("Ni-NTA Agarose (pre-equilibrated)", "reagent", "2 mL bed"),
            _io("Binding Buffer", "buffer", None, "10 mM imidazole"),
        ],
        "parameters": [
            _param("Mode", "Gravity flow / batch binding"),
            _param("Incubation", "30 min, 4 C"),
        ],
        "outputs": [
            _io("Tag-free ANC2 (flow-through)", "sample"),
            _io("His-SUMO + ULP1 (bound)", "waste"),
        ],
        "notes": "",
    },
    {
        "id": "b1-08",
        "order_index": 8,
        "label": "SDS-PAGE",
        "sublabel": "Check cleavage & purity",
        "status_template": "pending",
        "duration": "2 hr",
        "procedure_markdown": "Run SDS-PAGE to verify tag removal and estimate purity before concentration.",
        "inputs": [
            _io("ANC2 flow-through", "sample", "10 uL"),
            _io("12% polyacrylamide gel", "equipment"),
            _io("Protein Ladder (3-250 kDa)", "reagent", "5 uL"),
        ],
        "parameters": [
            _param("Voltage", "200 V, 45 min"),
            _param("Expected band", "~12-15 kDa (ANC2)"),
        ],
        "outputs": [
            _io("Gel image (.tiff)", "data"),
            _io("Purity assessment", "data", None, ">80% to proceed"),
        ],
        "notes": "",
    },
    {
        "id": "b1-09",
        "order_index": 9,
        "label": "Concentrate",
        "status_template": "pending",
        "duration": "1 hr",
        "procedure_markdown": "Concentrate the pooled sample to a SEC-compatible volume and concentration.",
        "inputs": [
            _io("ANC2 pool", "sample"),
            _io("Amicon Ultra-15 MWCO 10 kDa", "equipment"),
        ],
        "parameters": [
            _param("Speed", "3,000 x g"),
            _param("Target", "5-10 mg/mL"),
            _param("Final vol", "~1-2 mL"),
        ],
        "outputs": [
            _io("Concentrated ANC2", "sample"),
        ],
        "notes": "",
    },
    {
        "id": "b1-10",
        "order_index": 10,
        "label": "Preparative SEC",
        "sublabel": "Gel Filtration",
        "status_template": "pending",
        "duration": "4 hr",
        "procedure_markdown": "Inject concentrated ANC2 onto Superdex 75 and collect the symmetric monodisperse peak.",
        "inputs": [
            _io("Concentrated ANC2", "sample", "<=500 uL"),
            _io("Superdex 75 16/600", "equipment", None, "120 mL bed"),
            _io("SEC Running Buffer", "buffer", "500 mL", "20 mM HEPES pH 7.5, 150 mM NaCl, 1 mM DTT"),
        ],
        "parameters": [
            _param("Flow rate", "1 mL/min"),
            _param("Predicted elution", "~75 mL"),
        ],
        "outputs": [
            _io("SEC peak fractions", "sample"),
            _io("A280 chromatogram", "data"),
        ],
        "notes": "Collect symmetric peak fractions only.",
    },
    {
        "id": "b1-11",
        "order_index": 11,
        "label": "Collect Fractions",
        "sublabel": "~75 mL predicted elution",
        "status_template": "pending",
        "duration": "30 min",
        "procedure_markdown": "Pool the desired SEC fractions for final QC.",
        "inputs": [
            _io("SEC peak fractions", "sample"),
        ],
        "parameters": [
            _param("Criterion", "A280 peak only"),
            _param("Pool volume", "~5-8 mL"),
        ],
        "outputs": [
            _io("Pooled peak fractions", "sample"),
        ],
        "notes": "",
    },
    {
        "id": "b1-12",
        "order_index": 12,
        "label": "SDS-PAGE",
        "sublabel": "Final purity check",
        "status_template": "pending",
        "duration": "2 hr",
        "procedure_markdown": "Run a final purity gel on the pooled SEC fractions.",
        "inputs": [
            _io("Pooled SEC fractions", "sample", "10 uL/lane"),
            _io("12% SDS-PAGE gel", "equipment"),
        ],
        "parameters": [
            _param("Expected band", "~12-15 kDa"),
            _param("Purity threshold", ">95%"),
        ],
        "outputs": [
            _io("Final purity gel image", "data"),
            _io("Final concentration (A280)", "data"),
        ],
        "notes": "",
    },
    {
        "id": "b1-13",
        "order_index": 13,
        "label": "Pure ANC2",
        "sublabel": "Final product",
        "status_template": "pending",
        "duration": "--",
        "procedure_markdown": "Aliquot and flash-freeze the final purified sample.",
        "inputs": [
            _io("Purified ANC2 fractions", "sample"),
            _io("Protein LoBind tubes", "equipment"),
        ],
        "parameters": [
            _param("Aliquot size", "50-100 uL"),
            _param("Storage", "-80 C, flash-frozen"),
        ],
        "outputs": [
            _io("Pure ANC2 (flash-frozen aliquots)", "sample"),
            _io("Yield report", "data"),
        ],
        "notes": "",
    },
]


ANC2_BATCH_2_STEPS = [
    {
        "id": "b2-01",
        "order_index": 1,
        "label": "Cell Lysis",
        "sublabel": "Denaturing conditions",
        "status_template": "pending",
        "duration": "2 hr",
        "procedure_markdown": "Lyse under denaturing conditions to solubilize inclusion bodies.",
        "inputs": [
            _io("E. coli pellet (His-SUMO-ANC2)", "sample", "~8 g"),
            _io("Denaturing Lysis Buffer", "buffer", "40 mL", "50 mM Tris pH 8, 300 mM NaCl, 10 mM imidazole, 8 M urea"),
        ],
        "parameters": [
            _param("Sonication", "6x30s on/60s off"),
            _param("Centrifugation", "15,000 x g, 30 min"),
        ],
        "outputs": [
            _io("Denatured lysate (Sup 1)", "sample"),
            _io("Insoluble pellet", "waste"),
        ],
        "notes": "Denaturing lysis to solubilize inclusion bodies.",
    },
    {
        "id": "b2-02",
        "order_index": 2,
        "label": "Supernatant",
        "sublabel": "Sup 1 + Sup 2 + Refolded Fraction",
        "status_template": "pending",
        "duration": "1 hr",
        "procedure_markdown": "Pool the denatured soluble material and any successful recovery fractions.",
        "inputs": [
            _io("Denatured lysate", "sample"),
            _io("Wash Buffer (8 M urea)", "buffer"),
        ],
        "parameters": [
            _param("Sup 2", "Re-extract pellet in denaturing buffer"),
            _param("Pool", "Sup 1 + Sup 2 + refolded fraction"),
        ],
        "outputs": [
            _io("Combined denatured supernatant", "sample"),
        ],
        "notes": "",
    },
    {
        "id": "b2-03",
        "order_index": 3,
        "label": "Ni-NTA Affinity Column",
        "sublabel": "Protein binds Ni resin",
        "status_template": "pending",
        "duration": "3 hr",
        "procedure_markdown": "Bind the denatured fusion protein to Ni-NTA under high urea conditions.",
        "inputs": [
            _io("Combined denatured sup", "sample"),
            _io("Ni-NTA Agarose", "reagent", "5 mL bed"),
            _io("Denaturing Binding Buffer", "buffer", None, "8 M urea, 10 mM imidazole"),
        ],
        "parameters": [
            _param("Flow rate", "0.5-1 mL/min"),
            _param("Note", "His-tag binds under denaturing conditions"),
        ],
        "outputs": [
            _io("Denatured His-SUMO-ANC2 (bound)", "sample"),
            _io("Unbound contaminants", "waste"),
        ],
        "notes": "",
    },
    {
        "id": "b2-04",
        "order_index": 4,
        "label": "Elution",
        "sublabel": "Imidazole Buffer",
        "status_template": "pending",
        "duration": "1 hr",
        "procedure_markdown": "Elute the denatured fusion protein from Ni-NTA with imidazole.",
        "inputs": [
            _io("Bound protein on Ni-NTA", "sample"),
            _io("Denaturing Elution Buffer", "buffer", None, "8 M urea, 250 mM imidazole"),
        ],
        "parameters": [
            _param("Imidazole", "250 mM"),
            _param("Volume", "~10-15 mL"),
        ],
        "outputs": [
            _io("Denatured His-SUMO-ANC2 eluate", "sample"),
        ],
        "notes": "",
    },
    {
        "id": "b2-05",
        "order_index": 5,
        "label": "Dialysis",
        "sublabel": "Against 8.3% Acetic Acid",
        "status_template": "pending",
        "duration": "Overnight",
        "procedure_markdown": "Dialyze into acetic acid to precipitate contaminants before refolding.",
        "inputs": [
            _io("Denatured eluate", "sample"),
            _io("8.3% Acetic Acid", "buffer", "2x2 L"),
            _io("Dialysis Tubing MWCO 3.5 kDa", "equipment"),
        ],
        "parameters": [
            _param("Dialysate", "8.3% acetic acid (v/v)"),
            _param("Duration", "Overnight, 4 C"),
        ],
        "outputs": [
            _io("Acid-treated sample", "sample"),
            _io("Precipitated contaminants", "waste"),
        ],
        "notes": "Acetic acid selectively precipitates E. coli contaminants. Centrifuge after dialysis.",
    },
    {
        "id": "b2-06",
        "order_index": 6,
        "label": "Protein Refolding",
        "sublabel": "+100 mM NaCl additive",
        "status_template": "pending",
        "duration": "Overnight",
        "procedure_markdown": "Refold by stepwise buffer exchange and include an extra NaCl increment to reduce aggregation.",
        "inputs": [
            _io("Clarified acid-treated sample", "sample"),
            _io("Refolding Buffer", "buffer", None, "50 mM Tris pH 8, 150 mM NaCl, 1 mM DTT"),
            _io("NaCl additive", "reagent", "+100 mM final"),
        ],
        "parameters": [
            _param("Method", "Stepwise dialysis into refolding buffer"),
            _param("NaCl additive", "+100 mM"),
            _param("Temp", "4 C"),
        ],
        "outputs": [
            _io("Refolded His-SUMO-ANC2", "sample"),
            _io("Aggregate fraction", "waste"),
        ],
        "notes": "+100 mM NaCl reduces non-specific electrostatic interactions during refolding.",
    },
    {
        "id": "b2-07",
        "order_index": 7,
        "label": "Concentrate Sample",
        "sublabel": "Final Volume = 20 mL, ~200 mM NaCl",
        "status_template": "pending",
        "duration": "1 hr",
        "procedure_markdown": "Concentrate the refolded sample before rejoining the standard workflow.",
        "inputs": [
            _io("Refolded His-SUMO-ANC2", "sample"),
            _io("Amicon Ultra-15 MWCO 10 kDa", "equipment"),
        ],
        "parameters": [
            _param("Target volume", "20 mL"),
            _param("NaCl final", "~200 mM"),
        ],
        "outputs": [
            _io("Concentrated ANC2 (20 mL)", "sample", None, "Rejoins standard protocol"),
        ],
        "notes": "Standard protocol resumes here.",
    },
    {
        "id": "b2-08",
        "order_index": 8,
        "label": "ULFS Cleavage",
        "sublabel": "Remove tag",
        "status_template": "pending",
        "duration": "Overnight",
        "procedure_markdown": "Remove the fusion tag after refolding and buffer normalization.",
        "inputs": [
            _io("Refolded His-SUMO-ANC2 (post-exchange)", "sample"),
            _io("SUMO Protease ULP1/ULFS", "reagent", "1:100 w/w"),
        ],
        "parameters": [
            _param("Ratio", "1:100 (w/w)"),
            _param("Temp", "4 C"),
            _param("Duration", "16 hr"),
        ],
        "outputs": [
            _io("Cleaved ANC2 (tag-free)", "sample"),
            _io("Free His-SUMO tag", "sample"),
        ],
        "notes": "",
    },
    {
        "id": "b2-09",
        "order_index": 9,
        "label": "SP Sepharose Ion Exchange",
        "sublabel": "Buffer A: 25 mM NaCl · Buffer B: 1 M NaCl",
        "status_template": "pending",
        "duration": "3 hr",
        "procedure_markdown": "Use cation exchange to separate ANC2 from tag and contaminants after cleavage.",
        "inputs": [
            _io("Cleaved ANC2 mixture", "sample"),
            _io("HiTrap SP HP 5 mL", "equipment"),
            _io("Buffer A", "buffer", None, "50 mM Tris pH 8, 25 mM NaCl"),
            _io("Buffer B", "buffer", None, "50 mM Tris pH 8, 1 M NaCl"),
        ],
        "parameters": [
            _param("Equilibration", "5 CV Buffer A"),
            _param("Gradient", "0-100% B over 20 CV"),
            _param("Flow rate", "2 mL/min"),
        ],
        "outputs": [
            _io("Purified ANC2 fractions (IEX)", "sample"),
            _io("IEX chromatogram", "data"),
        ],
        "notes": "Cation exchange separates tag-free ANC2 from His-SUMO and contaminants.",
    },
    {
        "id": "b2-10",
        "order_index": 10,
        "label": "Purified Protein",
        "sublabel": "Final product (Batch 2)",
        "status_template": "pending",
        "duration": "--",
        "procedure_markdown": "Aliquot and freeze the purified Batch 2 material.",
        "inputs": [
            _io("ANC2 from SP Sepharose", "sample"),
            _io("Protein LoBind tubes", "equipment"),
        ],
        "parameters": [
            _param("Aliquot size", "50-100 uL"),
            _param("Storage", "-80 C, flash-frozen in LN2"),
        ],
        "outputs": [
            _io("Pure ANC2 Batch 2 (aliquots)", "sample"),
            _io("Final yield report", "data"),
        ],
        "notes": "",
    },
]


def _ensure_mock_user(db: Session) -> User:
    settings = get_settings()
    user = db.get(User, settings.mock_user_id)
    if user is None:
        user = User(
            id=settings.mock_user_id,
            email="chen@nmr-lab.local",
            display_name="Chen, Y.",
            role=settings.mock_user_role,
            lab_id="local-lab",
        )
        db.add(user)
        db.flush()
    return user


def _ensure_lab_member(
    db: Session,
    user_id: str,
    email: str,
    display_name: str,
    role: str,
    lab_id: str = "local-lab",
) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            email=email,
            display_name=display_name,
            role=role,
            lab_id=lab_id,
        )
        db.add(user)
        db.flush()
    return user


def _ensure_anc2_project(db: Session, owner_id: str) -> Project:
    project = db.scalar(select(Project).where(Project.code == "ANC2-PURIF-2026"))
    if project is None:
        project = Project(
            id="project-anc2",
            title="ANC2 Protein Purification",
            code="ANC2-PURIF-2026",
            description="Comparative purification strategies for ancestral ANC2 protein using native and refolding protocols.",
            owner_id=owner_id,
            status="active",
            tags=["protein", "purification", "anc2"],
        )
        db.add(project)
        db.flush()
    return project


def _seed_workflow(db: Session, owner_id: str, workflow_id: str, title: str, description: str, tags: list[str], steps: list[dict]) -> None:
    existing = db.get(Workflow, workflow_id)
    if existing is not None:
        return

    workflow = Workflow(
        id=workflow_id,
        title=title,
        description=description,
        owner_id=owner_id,
        visibility="library",
        library_state="published",
        version=1,
        tags=tags,
    )
    db.add(workflow)
    db.flush()

    for step in steps:
        db.add(
            WorkflowStep(
                id=step["id"],
                workflow_id=workflow.id,
                order_index=step["order_index"],
                label=step["label"],
                sublabel=step.get("sublabel"),
                status_template=step["status_template"],
                duration=step.get("duration"),
                procedure_markdown=step.get("procedure_markdown", ""),
                inputs=step.get("inputs", []),
                parameters=step.get("parameters", []),
                outputs=step.get("outputs", []),
                notes=step.get("notes", ""),
            )
        )


def _ensure_chat_channel(
    db: Session,
    channel_id: str,
    lab_id: str,
    name: str,
    topic: str,
    created_by_id: str,
) -> ChatChannel:
    channel = db.get(ChatChannel, channel_id)
    if channel is None:
        channel = ChatChannel(
            id=channel_id,
            lab_id=lab_id,
            name=name,
            topic=topic,
            created_by_id=created_by_id,
        )
        db.add(channel)
        db.flush()
    return channel


def _ensure_chat_message(
    db: Session,
    message_id: str,
    channel_id: str,
    lab_id: str,
    author_id: str,
    body: str,
    referenced_workflow_id: Optional[str] = None,
    referenced_experiment_id: Optional[str] = None,
) -> None:
    message = db.get(ChatMessage, message_id)
    if message is None:
        db.add(
            ChatMessage(
                id=message_id,
                channel_id=channel_id,
                lab_id=lab_id,
                author_id=author_id,
                body=body,
                referenced_workflow_id=referenced_workflow_id,
                referenced_experiment_id=referenced_experiment_id,
            )
        )


def seed_reference_data(db: Session) -> None:
    owner = _ensure_mock_user(db)
    ferretti = _ensure_lab_member(
        db,
        "user-pi-ferretti",
        "ferretti@nmr-lab.local",
        "Ferretti, A.",
        "professor",
    )
    okafor = _ensure_lab_member(
        db,
        "user-postdoc-okafor",
        "okafor@nmr-lab.local",
        "Okafor, M.",
        "post_doc",
    )
    _ensure_anc2_project(db, owner.id)

    _seed_workflow(
        db,
        owner.id,
        "workflow-anc2-batch-1",
        "ANC2 Batch 1",
        "No refolding workflow for native-condition ANC2 purification.",
        ["anc2", "batch-1", "purification", "workflow-library"],
        ANC2_BATCH_1_STEPS,
    )
    _seed_workflow(
        db,
        owner.id,
        "workflow-anc2-batch-2",
        "ANC2 Batch 2",
        "Refolding protocol workflow for ANC2 purification under denaturing/recovery conditions.",
        ["anc2", "batch-2", "purification", "workflow-library"],
        ANC2_BATCH_2_STEPS,
    )

    general_channel = _ensure_chat_channel(
        db,
        "channel-general",
        owner.lab_id,
        "general",
        "Lab-wide coordination, quick updates, and scheduling notes.",
        ferretti.id,
    )
    anc2_channel = _ensure_chat_channel(
        db,
        "channel-anc2",
        owner.lab_id,
        "anc2-purification",
        "Discussion for ANC2 workflows, purification troubleshooting, and run context.",
        owner.id,
    )
    _ensure_chat_message(
        db,
        "message-general-01",
        general_channel.id,
        owner.lab_id,
        ferretti.id,
        "Use this channel for high-level lab coordination. Workflow-specific troubleshooting should go into the relevant experiment channels.",
    )
    _ensure_chat_message(
        db,
        "message-anc2-01",
        anc2_channel.id,
        owner.lab_id,
        owner.id,
        "Batch 1 dialysis is still the key inflection point. Keep notes here if imidazole removal triggers precipitation again.",
        referenced_workflow_id="workflow-anc2-batch-1",
    )
    _ensure_chat_message(
        db,
        "message-anc2-02",
        anc2_channel.id,
        owner.lab_id,
        okafor.id,
        "If Batch 2 refolding improves solubility, record the NaCl increment and which fractions stayed monodisperse.",
        referenced_workflow_id="workflow-anc2-batch-2",
    )

    db.commit()
