from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from .database import get_db
from .deps import get_current_user
from .models import Assignment, ChemicalShift, Peak, Spectrum
from .schemas import AssignmentCreate, AssignmentRead, ChemicalShiftCreate, ChemicalShiftRead, PeakCreate, PeakRead, SpectrumCreate, SpectrumRead
from .services import nmr_spectral as service

router = APIRouter(prefix="/api/v1/nmr", tags=["nmr-spectral"])
def _values(item): return {column.name: getattr(item, column.name) for column in item.__table__.columns}
def _spectrum(db, item: Spectrum): return SpectrumRead(**_values(item), peak_count=service.peak_count(db, item.id))
def _peak(db, item: Peak): return PeakRead(**_values(item), assignment_count=service.assignment_count(db, item.id))
def _assignment(item: Assignment): return AssignmentRead(**_values(item))
def _shift(item: ChemicalShift): return ChemicalShiftRead(**_values(item))

@router.get("/spectra", response_model=list[SpectrumRead])
def list_spectra(sample_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    user=get_current_user(db); return [_spectrum(db,x) for x in service.list_spectra(db,user,sample_id)]
@router.post("/spectra", response_model=SpectrumRead, status_code=201)
def create_spectrum(payload:SpectrumCreate,db:Session=Depends(get_db)): return _spectrum(db,service.create_spectrum(db,get_current_user(db),payload))
@router.get("/spectra/{item_id}", response_model=SpectrumRead)
def get_spectrum(item_id:str,db:Session=Depends(get_db)): return _spectrum(db,service.get_spectrum(db,get_current_user(db),item_id))
@router.put("/spectra/{item_id}", response_model=SpectrumRead)
def update_spectrum(item_id:str,payload:SpectrumCreate,db:Session=Depends(get_db)): return _spectrum(db,service.update_spectrum(db,get_current_user(db),item_id,payload))
@router.delete("/spectra/{item_id}",status_code=204,response_class=Response)
def delete_spectrum(item_id:str,db:Session=Depends(get_db)): service.delete_spectrum(db,get_current_user(db),item_id); return Response(status_code=204)

@router.get("/peaks", response_model=list[PeakRead])
def list_peaks(spectrum_id:str=Query(min_length=1),db:Session=Depends(get_db)):
    user=get_current_user(db); return [_peak(db,x) for x in service.list_peaks(db,user,spectrum_id)]
@router.post("/peaks",response_model=PeakRead,status_code=201)
def create_peak(payload:PeakCreate,db:Session=Depends(get_db)): return _peak(db,service.create_peak(db,get_current_user(db),payload))
@router.get("/peaks/{item_id}",response_model=PeakRead)
def get_peak(item_id:str,db:Session=Depends(get_db)): return _peak(db,service.get_peak(db,get_current_user(db),item_id))
@router.put("/peaks/{item_id}",response_model=PeakRead)
def update_peak(item_id:str,payload:PeakCreate,db:Session=Depends(get_db)): return _peak(db,service.update_peak(db,get_current_user(db),item_id,payload))
@router.delete("/peaks/{item_id}",status_code=204,response_class=Response)
def delete_peak(item_id:str,db:Session=Depends(get_db)): service.delete_peak(db,get_current_user(db),item_id); return Response(status_code=204)

@router.get("/assignments",response_model=list[AssignmentRead])
def list_assignments(peak_id:str=Query(min_length=1),db:Session=Depends(get_db)):
    user=get_current_user(db); return [_assignment(x) for x in service.list_assignments(db,user,peak_id)]
@router.post("/assignments",response_model=AssignmentRead,status_code=201)
def create_assignment(payload:AssignmentCreate,db:Session=Depends(get_db)): return _assignment(service.create_assignment(db,get_current_user(db),payload))
@router.get("/assignments/{item_id}",response_model=AssignmentRead)
def get_assignment(item_id:str,db:Session=Depends(get_db)): return _assignment(service.get_assignment(db,get_current_user(db),item_id))
@router.put("/assignments/{item_id}",response_model=AssignmentRead)
def update_assignment(item_id:str,payload:AssignmentCreate,db:Session=Depends(get_db)): return _assignment(service.update_assignment(db,get_current_user(db),item_id,payload))
@router.delete("/assignments/{item_id}",status_code=204,response_class=Response)
def delete_assignment(item_id:str,db:Session=Depends(get_db)): service.delete_assignment(db,get_current_user(db),item_id); return Response(status_code=204)

@router.get("/chemical-shifts",response_model=list[ChemicalShiftRead])
def list_shifts(spectrum_id:Optional[str]=None,residue_id:Optional[str]=None,db:Session=Depends(get_db)):
    user=get_current_user(db); return [_shift(x) for x in service.list_shifts(db,user,spectrum_id,residue_id)]
@router.post("/chemical-shifts",response_model=ChemicalShiftRead,status_code=201)
def create_shift(payload:ChemicalShiftCreate,db:Session=Depends(get_db)): return _shift(service.create_shift(db,get_current_user(db),payload))
@router.get("/chemical-shifts/{item_id}",response_model=ChemicalShiftRead)
def get_shift(item_id:str,db:Session=Depends(get_db)): return _shift(service.get_shift(db,get_current_user(db),item_id))
@router.put("/chemical-shifts/{item_id}",response_model=ChemicalShiftRead)
def update_shift(item_id:str,payload:ChemicalShiftCreate,db:Session=Depends(get_db)): return _shift(service.update_shift(db,get_current_user(db),item_id,payload))
@router.delete("/chemical-shifts/{item_id}",status_code=204,response_class=Response)
def delete_shift(item_id:str,db:Session=Depends(get_db)): service.delete_shift(db,get_current_user(db),item_id); return Response(status_code=204)
