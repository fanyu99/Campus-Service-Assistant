from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback import submit_feedback

router = APIRouter(prefix="/api")


@router.post("/feedback", response_model=FeedbackResponse)
def post_feedback(
    payload: FeedbackRequest, db: Session = Depends(get_db)
) -> FeedbackResponse:
    submit_feedback(db, payload)
    return FeedbackResponse()