from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.models.user import User
from app.services.twilio_service import TwilioService
from app.core.config import settings

router = APIRouter()

_twilio_service = None


def get_twilio_service():
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioService()
    return _twilio_service


@router.post("/", response_model=schemas.Call)
def make_call(
    *,
    db: Session = Depends(deps.get_db),
    call_in: schemas.CallCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Make a new call
    """
    twilio_service = get_twilio_service()
    call_rate = twilio_service.get_call_rate(call_in.phone_number)
    if not call_rate:
        raise HTTPException(
            status_code=400,
            detail="Call rate not available for this number"
        )

    if current_user.balance < call_rate.rate:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance"
        )

    active_call = crud.call.get_active_call(db, user_id=current_user.id)
    if active_call:
        raise HTTPException(
            status_code=400,
            detail="User already has an active call"
        )

    call = crud.call.create_with_user(
        db=db, obj_in=call_in, user_id=current_user.id
    )

    try:
        twilio_call = twilio_service.make_call(
            to=call_in.phone_number,
            from_number=twilio_service.twilio_phone_number,
            callback_url=f"{settings.API_V1_STR}/calls/{call.id}/status"
        )

        call.twilio_call_sid = twilio_call.sid
        db.commit()

    except Exception as e:
        call.status = schemas.CallStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate call: {str(e)}"
        )

    return call


@router.get("/rates", response_model=List[schemas.CallRate])
def get_call_rates() -> Any:
    """
    Get call rates for different countries
    """
    twilio_service = get_twilio_service()
    return twilio_service.get_all_call_rates()


@router.get("/", response_model=List[schemas.Call])
def get_call_history(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get user's call history
    """
    calls = crud.call.get_user_calls(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return calls


@router.get("/{call_id}", response_model=schemas.Call)
def get_call(
    *,
    db: Session = Depends(deps.get_db),
    call_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get call by ID
    """
    call = crud.call.get(db=db, id=call_id)
    if not call:
        raise HTTPException(
            status_code=404,
            detail="Call not found"
        )
    if call.user_id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions"
        )
    return call


@router.post("/{call_id}/end")
def end_call(
    *,
    db: Session = Depends(deps.get_db),
    call_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    End an active call
    """
    twilio_service = get_twilio_service()
    call = crud.call.get(db=db, id=call_id)
    if not call:
        raise HTTPException(
            status_code=404,
            detail="Call not found"
        )
    if call.user_id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions"
        )
    if call.status != schemas.CallStatus.ONGOING:
        raise HTTPException(
            status_code=400,
            detail="Call is not active"
        )

    if call.twilio_call_sid:
        try:
            twilio_service.end_call(call.twilio_call_sid)
        except Exception as e:
            print(f"Failed to end Twilio call: {e}")

    call.status = schemas.CallStatus.COMPLETED
    db.commit()

    return {"message": "Call ended successfully"}
