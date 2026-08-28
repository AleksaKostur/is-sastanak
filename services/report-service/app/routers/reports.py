from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io

from ..database import get_db
from ..models import Meeting, Report, User
from ..schemas import ReportOut
from ..dependencies import get_current_user, AnyAuthenticated
from ..reports_data import gather_meeting_data
from ..generators import generate_pdf, generate_xlsx, generate_docx

router = APIRouter()

# mapiranje formata na generator + MIME tip + ekstenziju
FORMATS = {
    "PDF":  (generate_pdf,  "application/pdf", "pdf"),
    "XLSX": (generate_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "DOCX": (generate_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
}


@router.get("/meeting/{meeting_id}/export")
def export_report(
    meeting_id: int,
    format: str = "PDF",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generiše izveštaj (zapisnik) za sastanak u traženom formatu.
    Format: PDF (default), XLSX ili DOCX.
    """
    fmt = format.upper()
    if fmt not in FORMATS:
        raise HTTPException(400, f"Nepodržan format. Dozvoljeni: {', '.join(FORMATS.keys())}")

    data = gather_meeting_data(meeting_id, db)
    if data is None:
        raise HTTPException(404, "Sastanak ne postoji")

    generator, mime, ext = FORMATS[fmt]
    content = generator(data)

    # evidentiraj generisanje izveštaja
    report = Report(
        meeting_id=meeting_id,
        requested_by=current_user.id,
        report_type="ZAPISNIK",
        period=fmt,
    )
    db.add(report)
    db.commit()

    filename = f"zapisnik_sastanak_{meeting_id}.{ext}"
    return StreamingResponse(
        io.BytesIO(content),
        media_type=mime,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/", response_model=List[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    _=AnyAuthenticated,
):
    """Istorija generisanih izveštaja."""
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.get("/meeting/{meeting_id}", response_model=List[ReportOut])
def list_reports_for_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    _=AnyAuthenticated,
):
    """Izveštaji generisani za konkretan sastanak."""
    return db.query(Report).filter(
        Report.meeting_id == meeting_id
    ).order_by(Report.created_at.desc()).all()