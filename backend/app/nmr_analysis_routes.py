from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .deps import get_current_user
from .schemas import ChemicalShiftPerturbationRead, ChemicalShiftPerturbationRequest, SpectrumComparisonRead, SpectrumComparisonRequest
from .services import nmr_analysis

router=APIRouter(prefix="/api/v1/nmr/analyses",tags=["nmr-analysis"])

@router.post("/compare-spectra",response_model=SpectrumComparisonRead)
def compare_spectra(payload:SpectrumComparisonRequest,db:Session=Depends(get_db))->SpectrumComparisonRead:
    return nmr_analysis.compare_spectra(db,get_current_user(db),payload)

@router.post("/chemical-shift-perturbation",response_model=ChemicalShiftPerturbationRead)
def chemical_shift_perturbation(payload:ChemicalShiftPerturbationRequest,db:Session=Depends(get_db))->ChemicalShiftPerturbationRead:
    return nmr_analysis.calculate_csp(db,get_current_user(db),payload)
