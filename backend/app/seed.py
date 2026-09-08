from __future__ import annotations

from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .config import get_settings
from .models import (
    Attachment,
    ChatChannel,
    ChatMessage,
    Experiment,
    ExperimentStepRun,
    ExperimentWorkflowRun,
    Project,
    ProjectMember,
    User,
    Workflow,
    WorkflowBranch,
    WorkflowMember,
    WorkflowStep,
)


SHOWCASE_PROJECT_IDS = {"project-anc2", "project-rpc10", "project-ccl20", "project-shared-methods"}
STALE_PROJECT_PREFIXES = ("PR6 Sync Project", "SEC Optimization")
STALE_PROJECT_TITLES = {
    "BRCA1 Sanger Sequencing",
    "Histone H3 ChIP-seq",
    "NMR Structure of ANC2",
    "p53-DNA Binding Assay",
    "hi",
    "hii",
    "hiii",
}
STALE_PROJECT_CODE_PREFIXES = ("SYNC-", "SEC-", "XRAY", "BIND-", "GEN-", "EPIG-", "NMR-")


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


RPC10_TROUBLESHOOTING_STEPS = [
    {
        "id": "rpc10-01",
        "order_index": 1,
        "label": "Cell Lysis",
        "status_template": "running",
        "duration": "2 hr",
        "procedure_markdown": "Lyse the RPC10 expression pellet under the same base conditions used for Ni-NTA loading.",
        "inputs": [_io("RPC10 expression pellet", "sample"), _io("Native lysis buffer", "buffer", "40 mL")],
        "parameters": [_param("Temperature", "4 C"), _param("Clarification", "15,000 x g, 30 min")],
        "outputs": [_io("Clarified lysate", "sample")],
        "notes": "Start point for both troubleshooting branches.",
    },
    {
        "id": "rpc10-02",
        "order_index": 2,
        "label": "Ni-NTA Affinity Chromatography",
        "status_template": "pending",
        "duration": "3 hr",
        "procedure_markdown": "Bind His-SUMO-RPC10 to Ni-NTA and collect the imidazole eluate for split-batch troubleshooting.",
        "inputs": [_io("Clarified lysate", "sample"), _io("Ni-NTA resin", "reagent", "5 mL bed")],
        "parameters": [_param("Elution", "250 mM imidazole")],
        "outputs": [_io("RPC10 eluate", "sample")],
        "notes": "",
    },
    {
        "id": "rpc10-03",
        "order_index": 3,
        "label": "Split Into Two Batches",
        "status_template": "pending",
        "duration": "15 min",
        "procedure_markdown": "Divide the eluate into zinc-reduction and imidazole-rescue branches before continuing troubleshooting.",
        "inputs": [_io("RPC10 eluate", "sample")],
        "parameters": [_param("Branch A", "Zn2+ reduction dialysis"), _param("Branch B", "Imidazole rescue")],
        "outputs": [_io("Batch 1 aliquot", "sample"), _io("Batch 2 aliquot", "sample")],
        "notes": "Main branch point for RPC10 troubleshooting.",
    },
]


CCL20_TRANSFORMATION_STEPS = [
    {
        "id": "ccl20-01",
        "order_index": 1,
        "label": "Plasmid Containing Gene Of Interest",
        "status_template": "complete",
        "duration": "10 min",
        "procedure_markdown": "Prepare the verified plasmid DNA containing the gene of interest for transformation.",
        "inputs": [_io("Plasmid DNA", "sample", "15-20 ng")],
        "parameters": [_param("Quality", "Sequence-verified plasmid")],
        "outputs": [_io("Transformation-ready plasmid", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-02",
        "order_index": 2,
        "label": "Competent BL21 E. coli Cells",
        "sublabel": "Thawed on ice",
        "status_template": "running",
        "duration": "20 min",
        "procedure_markdown": "Thaw competent BL21 cells on ice and keep cold until DNA addition.",
        "inputs": [_io("Competent BL21 cells", "sample")],
        "parameters": [_param("Handling", "Keep on ice")],
        "outputs": [_io("Thawed competent cells", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-03",
        "order_index": 3,
        "label": "Add Plasmid DNA",
        "status_template": "pending",
        "duration": "5 min",
        "procedure_markdown": "Add plasmid DNA to the competent cells without pipetting aggressively.",
        "inputs": [_io("Thawed competent cells", "sample"), _io("Transformation-ready plasmid", "sample", "15-20 ng")],
        "parameters": [_param("Mixing", "Gentle flick")],
        "outputs": [_io("DNA/cell mix", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-04",
        "order_index": 4,
        "label": "Incubate On Ice",
        "status_template": "pending",
        "duration": "20 min",
        "procedure_markdown": "Allow the plasmid to associate with the competent cells on ice.",
        "inputs": [_io("DNA/cell mix", "sample")],
        "parameters": [_param("Time", "~20 min")],
        "outputs": [_io("Pre-heat-shock mixture", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-05",
        "order_index": 5,
        "label": "Heat Shock",
        "status_template": "pending",
        "duration": "45 sec",
        "procedure_markdown": "Heat shock the cells at 42 C and immediately return them to ice.",
        "inputs": [_io("Pre-heat-shock mixture", "sample")],
        "parameters": [_param("Temperature", "42 C"), _param("Time", "45 sec")],
        "outputs": [_io("Heat-shocked cells", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-06",
        "order_index": 6,
        "label": "Return To Ice",
        "status_template": "pending",
        "duration": "2 min",
        "procedure_markdown": "Cool the cells immediately after heat shock.",
        "inputs": [_io("Heat-shocked cells", "sample")],
        "parameters": [_param("Time", "~2 min")],
        "outputs": [_io("Recovered heat-shocked cells", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-07",
        "order_index": 7,
        "label": "Add LB Broth",
        "status_template": "pending",
        "duration": "5 min",
        "procedure_markdown": "Add recovery medium to the cells before outgrowth.",
        "inputs": [_io("Recovered heat-shocked cells", "sample"), _io("LB broth", "buffer", "~900 uL")],
        "parameters": [_param("Volume", "~900 uL")],
        "outputs": [_io("Recovery culture", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-08",
        "order_index": 8,
        "label": "Recovery Incubation",
        "status_template": "pending",
        "duration": "45-60 min",
        "procedure_markdown": "Recover transformed cells in LB before plating.",
        "inputs": [_io("Recovery culture", "sample")],
        "parameters": [_param("Temp", "37 C"), _param("Shaking", "220 rpm")],
        "outputs": [_io("Recovered transformants", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-09",
        "order_index": 9,
        "label": "Centrifuge Cells",
        "sublabel": "Pellet bacteria",
        "status_template": "pending",
        "duration": "10 min",
        "procedure_markdown": "Pellet the cells and remove most of the supernatant to concentrate before plating.",
        "inputs": [_io("Recovered transformants", "sample")],
        "parameters": [_param("Goal", "Concentrate cells before plating")],
        "outputs": [_io("Cell pellet", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-10",
        "order_index": 10,
        "label": "Plate On LB Agar",
        "sublabel": "Correct antibiotic",
        "status_template": "pending",
        "duration": "15 min",
        "procedure_markdown": "Resuspend the pellet in residual volume and plate on antibiotic-selective LB agar.",
        "inputs": [_io("Cell pellet", "sample"), _io("LB agar plate + antibiotic", "equipment")],
        "parameters": [_param("Selection", "Correct antibiotic for plasmid")],
        "outputs": [_io("Transformation plate", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-11",
        "order_index": 11,
        "label": "Overnight Incubation",
        "status_template": "pending",
        "duration": "Overnight",
        "procedure_markdown": "Incubate the transformation plate overnight at 37 C.",
        "inputs": [_io("Transformation plate", "sample")],
        "parameters": [_param("Temp", "37 C")],
        "outputs": [_io("Colonies form", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-12",
        "order_index": 12,
        "label": "Pick Colony",
        "status_template": "pending",
        "duration": "15 min",
        "procedure_markdown": "Pick an isolated colony and inoculate a starter culture.",
        "inputs": [_io("Colonies form", "sample")],
        "parameters": [_param("Selection", "Well-isolated colony")],
        "outputs": [_io("Picked colony", "sample")],
        "notes": "",
    },
    {
        "id": "ccl20-13",
        "order_index": 13,
        "label": "Starter Culture / Expression Test",
        "status_template": "pending",
        "duration": "Overnight",
        "procedure_markdown": "Grow the starter culture and begin small-scale expression profiling.",
        "inputs": [_io("Picked colony", "sample"), _io("LB + antibiotic", "buffer")],
        "parameters": [_param("Next step", "Expression profiling / protein expression test")],
        "outputs": [_io("Starter culture", "sample")],
        "notes": "",
    },
]


REVERSE_NICKEL_STANDARD_STEPS = [
    {
        "id": "std-rni-01",
        "order_index": 1,
        "label": "Equilibrate Reverse Ni-NTA",
        "status_template": "pending",
        "duration": "20 min",
        "procedure_markdown": "Prepare Ni-NTA in low-imidazole binding buffer for the reverse-capture cleanup step.",
        "inputs": [_io("Ni-NTA resin", "reagent", "2 mL bed"), _io("Binding buffer", "buffer", "10 mM imidazole")],
        "parameters": [_param("Temperature", "4 C")],
        "outputs": [_io("Equilibrated resin", "sample")],
        "notes": "",
    },
    {
        "id": "std-rni-02",
        "order_index": 2,
        "label": "Load Cleavage Mixture",
        "status_template": "pending",
        "duration": "30 min",
        "procedure_markdown": "Incubate the cleavage mixture with Ni-NTA so His-tagged components bind while cleaved target remains untagged.",
        "inputs": [_io("Cleavage mixture", "sample"), _io("Equilibrated resin", "sample")],
        "parameters": [_param("Mode", "Batch bind or gravity flow")],
        "outputs": [_io("Bound resin with His-tagged species", "sample")],
        "notes": "",
    },
    {
        "id": "std-rni-03",
        "order_index": 3,
        "label": "Collect Flow-Through",
        "status_template": "pending",
        "duration": "20 min",
        "procedure_markdown": "Collect the flow-through containing the cleaved target protein.",
        "inputs": [_io("Loaded reverse Ni-NTA resin", "sample")],
        "parameters": [_param("Expected", "Cleaved target in flow-through")],
        "outputs": [_io("Tag-free protein", "sample"), _io("His-tagged contaminants retained", "waste")],
        "notes": "",
    },
]


ION_EXCHANGE_STANDARD_STEPS = [
    {
        "id": "std-iex-01",
        "order_index": 1,
        "label": "Prepare Low-Salt Start Buffer",
        "status_template": "pending",
        "duration": "30 min",
        "procedure_markdown": "Exchange the sample into a low-salt start buffer compatible with the chosen ion-exchange resin.",
        "inputs": [_io("Protein sample", "sample"), _io("Start buffer", "buffer", "25 mM NaCl")],
        "parameters": [_param("Goal", "Match conductivity to start buffer")],
        "outputs": [_io("Buffer-exchanged sample", "sample")],
        "notes": "",
    },
    {
        "id": "std-iex-02",
        "order_index": 2,
        "label": "Equilibrate Column",
        "status_template": "pending",
        "duration": "20 min",
        "procedure_markdown": "Equilibrate the ion-exchange column in start buffer before loading the sample.",
        "inputs": [_io("IEX column", "equipment"), _io("Start buffer", "buffer")],
        "parameters": [_param("Column example", "SP Sepharose")],
        "outputs": [_io("Equilibrated IEX column", "sample")],
        "notes": "",
    },
    {
        "id": "std-iex-03",
        "order_index": 3,
        "label": "Load And Elute Gradient",
        "status_template": "pending",
        "duration": "2 hr",
        "procedure_markdown": "Load the sample and run a salt gradient to resolve the target from contaminants.",
        "inputs": [_io("Buffer-exchanged sample", "sample"), _io("Buffer A", "buffer", "25 mM NaCl"), _io("Buffer B", "buffer", "1 M NaCl")],
        "parameters": [_param("Gradient", "0-100% B"), _param("Monitor", "A280 and conductivity")],
        "outputs": [_io("IEX fractions", "sample"), _io("Chromatogram", "data")],
        "notes": "",
    },
    {
        "id": "std-iex-04",
        "order_index": 4,
        "label": "Analyze Fractions",
        "status_template": "pending",
        "duration": "1 hr",
        "procedure_markdown": "Check fractions by SDS-PAGE and pool the appropriate purified target fractions.",
        "inputs": [_io("IEX fractions", "sample"), _io("SDS-PAGE gel", "equipment")],
        "parameters": [_param("Selection", "Pool pure target fractions only")],
        "outputs": [_io("Pooled purified sample", "sample")],
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
    return _ensure_project(
        db,
        project_id="project-anc2",
        title="ANC2 Protein Purification",
        code="ANC2-PURIF-2026",
        description="Comparative purification strategies for ancestral ANC2 protein using native and refolding protocols.",
        owner_id=owner_id,
        status="active",
        tags=["protein", "purification", "anc2"],
    )


def _ensure_project(
    db: Session,
    *,
    project_id: str,
    title: str,
    code: str,
    description: str,
    owner_id: str,
    status: str,
    tags: list[str],
) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        project = db.scalar(select(Project).where(Project.code == code))
    if project is None:
        project = Project(
            id=project_id,
            title=title,
            code=code,
            description=description,
            owner_id=owner_id,
            status=status,
            tags=tags,
        )
        db.add(project)
        db.flush()
    else:
        project.id = project_id
        project.title = title
        project.code = code
        project.description = description
        project.owner_id = owner_id
        project.status = status
        project.tags = tags
    return project


def _delete_workflow_data(db: Session, workflow: Workflow) -> None:
    _delete_workflow_children(db, workflow)
    db.delete(workflow)


def _delete_workflow_children(db: Session, workflow: Workflow) -> None:
    step_ids = db.scalars(select(WorkflowStep.id).where(WorkflowStep.workflow_id == workflow.id)).all()
    if step_ids:
        db.execute(delete(Attachment).where(Attachment.owner_type == "workflow_step", Attachment.owner_id.in_(step_ids)))
    db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id, WorkflowStep.workflow_branch_id.is_not(None)))
    db.execute(delete(WorkflowBranch).where(WorkflowBranch.workflow_id == workflow.id))
    db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id))
    db.execute(delete(WorkflowMember).where(WorkflowMember.workflow_id == workflow.id))


def _delete_project_data(db: Session, project: Project) -> None:
    for workflow in db.scalars(select(Workflow).where(Workflow.project_id == project.id)).all():
        _delete_workflow_data(db, workflow)

    for experiment in db.scalars(select(Experiment).where(Experiment.project_id == project.id)).all():
        workflow_runs = db.scalars(select(ExperimentWorkflowRun).where(ExperimentWorkflowRun.experiment_id == experiment.id)).all()
        workflow_run_ids = [workflow_run.id for workflow_run in workflow_runs]
        if workflow_run_ids:
            step_run_ids = db.scalars(
                select(ExperimentStepRun.id).where(ExperimentStepRun.experiment_workflow_run_id.in_(workflow_run_ids))
            ).all()
            if step_run_ids:
                db.execute(delete(Attachment).where(Attachment.owner_type == "experiment_step_run", Attachment.owner_id.in_(step_run_ids)))
            db.execute(delete(ExperimentStepRun).where(ExperimentStepRun.experiment_workflow_run_id.in_(workflow_run_ids)))
            db.execute(delete(ExperimentWorkflowRun).where(ExperimentWorkflowRun.id.in_(workflow_run_ids)))
        db.delete(experiment)

    db.execute(delete(ProjectMember).where(ProjectMember.project_id == project.id))
    db.delete(project)


def _is_stale_demo_project(project: Project) -> bool:
    if project.id in SHOWCASE_PROJECT_IDS:
        return False
    title = project.title or ""
    code = project.code or ""
    return (
        title in STALE_PROJECT_TITLES
        or title.startswith(STALE_PROJECT_PREFIXES)
        or code.startswith(STALE_PROJECT_CODE_PREFIXES)
    )


def _cleanup_stale_showcase_data(db: Session) -> None:
    for project in db.scalars(select(Project)).all():
        if _is_stale_demo_project(project):
            _delete_project_data(db, project)


def _ensure_project_member(db: Session, project_id: str, user_id: str, role: str) -> None:
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if membership is None:
        db.add(
            ProjectMember(
                id=f"project-member-{project_id}-{user_id}",
                project_id=project_id,
                user_id=user_id,
                role=role,
            )
        )
    else:
        membership.role = role


def _ensure_workflow_member(db: Session, workflow_id: str, user_id: str, role: str) -> None:
    membership = db.scalar(
        select(WorkflowMember).where(
            WorkflowMember.workflow_id == workflow_id,
            WorkflowMember.user_id == user_id,
        )
    )
    if membership is None:
        db.add(
            WorkflowMember(
                id=f"workflow-member-{workflow_id}-{user_id}",
                workflow_id=workflow_id,
                user_id=user_id,
                role=role,
            )
        )
    else:
        membership.role = role


def _seed_workflow(
    db: Session,
    owner_id: str,
    workflow_id: str,
    title: str,
    description: str,
    tags: list[str],
    steps: list[dict],
    *,
    project_id: Optional[str] = None,
    visibility: str = "library",
    library_state: str = "published",
    reset_steps: bool = True,
) -> None:
    existing = db.get(Workflow, workflow_id)
    if existing is not None:
        existing.title = title
        existing.description = description
        existing.owner_id = owner_id
        existing.project_id = project_id
        existing.visibility = visibility
        existing.library_state = library_state
        existing.tags = tags
        _ensure_workflow_member(db, existing.id, owner_id, "owner")
        if reset_steps:
            _delete_workflow_children(db, existing)
            workflow = existing
            _ensure_workflow_member(db, workflow.id, owner_id, "owner")
        else:
            return
    else:
        workflow = Workflow(
            id=workflow_id,
            title=title,
            description=description,
            owner_id=owner_id,
            project_id=project_id,
            visibility=visibility,
            library_state=library_state,
            version=1,
            tags=tags,
        )
        db.add(workflow)
        db.flush()
        _ensure_workflow_member(db, workflow.id, owner_id, "owner")

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
    _cleanup_stale_showcase_data(db)
    anc2_project = _ensure_anc2_project(db, owner.id)
    rpc10_project = _ensure_project(
        db,
        project_id="project-rpc10",
        title="RPC10 Purification Process And Troubleshooting",
        code="RPC10-PURIF-2026",
        description="Parallel troubleshooting routes for RPC10 purification, focusing on zinc reduction and imidazole-rescue decisions.",
        owner_id=owner.id,
        status="active",
        tags=["rpc10", "purification", "troubleshooting"],
    )
    ccl20_project = _ensure_project(
        db,
        project_id="project-ccl20",
        title="CCL20 Transformation And Culture",
        code="CCL20-TRANSFORM-2026",
        description="Bacterial transformation workflow for CCL20 plasmid handling, colony recovery, and starter culture preparation.",
        owner_id=owner.id,
        status="active",
        tags=["ccl20", "transformation", "cloning"],
    )
    shared_methods_project = _ensure_project(
        db,
        project_id="project-shared-methods",
        title="Shared Methods",
        code="SHARED-METHODS",
        description="Lab-wide standardized methods shared across protein workflow types.",
        owner_id=owner.id,
        status="active",
        tags=["shared", "standardized", "methods"],
    )
    _ensure_project_member(db, anc2_project.id, owner.id, "owner")
    _ensure_project_member(db, anc2_project.id, ferretti.id, "editor")
    _ensure_project_member(db, anc2_project.id, okafor.id, "commenter")
    _ensure_project_member(db, rpc10_project.id, owner.id, "owner")
    _ensure_project_member(db, rpc10_project.id, ferretti.id, "editor")
    _ensure_project_member(db, ccl20_project.id, owner.id, "owner")
    _ensure_project_member(db, ccl20_project.id, okafor.id, "viewer")
    _ensure_project_member(db, shared_methods_project.id, owner.id, "owner")

    # Standards created before type grouping remain discoverable in Shared Methods.
    for workflow in db.scalars(select(Workflow).where(Workflow.project_id.is_(None))).all():
        if "standardized" in workflow.tags:
            workflow.project_id = shared_methods_project.id

    _seed_workflow(
        db,
        owner.id,
        "workflow-anc2-batch-1",
        "ANC2 Batch 1",
        "No refolding workflow for native-condition ANC2 purification.",
        ["experimental", "anc2", "batch-1", "purification"],
        ANC2_BATCH_1_STEPS,
        project_id=anc2_project.id,
        visibility="private",
        library_state="draft",
    )
    _seed_workflow(
        db,
        owner.id,
        "workflow-anc2-batch-2",
        "ANC2 Batch 2",
        "Refolding protocol workflow for ANC2 purification under denaturing/recovery conditions.",
        ["experimental", "anc2", "batch-2", "purification"],
        ANC2_BATCH_2_STEPS,
        project_id=anc2_project.id,
        visibility="private",
        library_state="draft",
    )
    _ensure_workflow_member(db, "workflow-anc2-batch-1", ferretti.id, "editor")
    _ensure_workflow_member(db, "workflow-anc2-batch-1", okafor.id, "commenter")
    _ensure_workflow_member(db, "workflow-anc2-batch-2", ferretti.id, "editor")
    _ensure_workflow_member(db, "workflow-anc2-batch-2", okafor.id, "commenter")
    _seed_workflow(
        db,
        owner.id,
        "workflow-rpc10-troubleshooting",
        "RPC10 Purification / Troubleshooting",
        "Parallel troubleshooting routes for RPC10 after Ni-NTA elution.",
        ["experimental", "rpc10", "purification", "troubleshooting"],
        RPC10_TROUBLESHOOTING_STEPS,
        project_id=rpc10_project.id,
        visibility="private",
        library_state="draft",
    )
    _seed_workflow(
        db,
        owner.id,
        "workflow-ccl20-transformation",
        "CCL20 Transformation And Culture",
        "Bacterial transformation workflow from plasmid addition through colony pick and starter culture.",
        ["experimental", "ccl20", "transformation", "cloning"],
        CCL20_TRANSFORMATION_STEPS,
        project_id=ccl20_project.id,
        visibility="private",
        library_state="draft",
    )
    _seed_workflow(
        db,
        owner.id,
        "workflow-standard-reverse-nickel",
        "Reverse Nickel Chromatography",
        "Standardized reverse Ni-NTA cleanup workflow for post-cleavage His-tag removal.",
        ["standardized", "chromatography", "reverse-nickel"],
        REVERSE_NICKEL_STANDARD_STEPS,
        project_id=shared_methods_project.id,
    )
    _seed_workflow(
        db,
        owner.id,
        "workflow-standard-ion-exchange",
        "Ion Exchange Chromatography",
        "Standardized ion-exchange workflow for salt-gradient polishing and fraction selection.",
        ["standardized", "chromatography", "ion-exchange"],
        ION_EXCHANGE_STANDARD_STEPS,
        project_id=shared_methods_project.id,
    )
    _ensure_workflow_member(db, "workflow-standard-reverse-nickel", ferretti.id, "editor")
    _ensure_workflow_member(db, "workflow-standard-ion-exchange", ferretti.id, "editor")

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
