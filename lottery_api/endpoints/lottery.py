import os
from typing import List, Optional
from fastapi import APIRouter, Depends, status, File, UploadFile, Query, HTTPException, Path
from fastapi.responses import FileResponse
from lottery_api.data_access_object.db import get_db_connection
from lottery_api.business_model.lottery_business import LotteryBusiness
from lottery_api.lib.response import ExceptionResponse, SingleResponse, ListResponse, to_json_response
from lottery_api.schema.lottery import (
    LotteryEventCreate, LotteryEvent, LotteryEventType,
    StudentImport, StudentsImport, ParticipantList,
    PrizeCreate, PrizeSettings, PrizeList, Prize, PrizeUpdate,
    DrawRequest, WinnersList, ExportWinnersResponse, FinalParticipantList, ResetDrawingResponse,
    DeleteParticipantResponse, DeleteAllParticipantsResponse
)

router = APIRouter(prefix="/lottery", tags=["lottery"])


@router.post("/events", response_model=SingleResponse[LotteryEvent], status_code=status.HTTP_201_CREATED)
async def create_lottery_event(
        request: LotteryEventCreate,
        conn=Depends(get_db_connection)
):
    """Create a new lottery event"""
    result = await LotteryBusiness.create_lottery_event(conn, request)
    return to_json_response(SingleResponse(result=result))


@router.get("/events", response_model=ListResponse[LotteryEvent])
async def get_lottery_events(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        event_type: Optional[LotteryEventType] = None,
        conn=Depends(get_db_connection)
):
    """Get all lottery events with pagination"""
    result = await LotteryBusiness.get_lottery_events(conn, limit, offset, event_type.value if event_type else None)
    return to_json_response(ListResponse(result=result))


@router.get("/events/{event_id}", response_model=SingleResponse[LotteryEvent],
            responses={404: {'model': ExceptionResponse}})
async def get_lottery_event(
        event_id: str,
        conn=Depends(get_db_connection)
):
    """Get a lottery event by ID"""
    result = await LotteryBusiness.get_lottery_event(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.post("/events/{event_id}/participants", status_code=status.HTTP_201_CREATED,
             responses={404: {'model': ExceptionResponse}})
async def import_students_and_add_participants(
        event_id: str,
        request: StudentsImport,
        conn=Depends(get_db_connection)
):
    """Import students and add them as participants to a lottery event"""
    result = await LotteryBusiness.import_students_and_add_participants(
        conn, event_id, [student.dict() for student in request.students]
    )
    return to_json_response(ListResponse(result=result))


@router.get("/events/{event_id}/participants", response_model=SingleResponse[ParticipantList],
            responses={404: {'model': ExceptionResponse}})
async def get_participants(
        event_id: str,
        limit: int = Query(1000, ge=1, le=10000),
        offset: int = Query(0, ge=0),
        conn=Depends(get_db_connection)
):
    """Get participants for a lottery event"""
    result = await LotteryBusiness.get_participants(conn, event_id, limit, offset)
    return to_json_response(SingleResponse(result=result))


@router.post("/events/{event_id}/prizes", response_model=ListResponse[Prize],
             responses={404: {'model': ExceptionResponse}})
async def set_prizes(
        event_id: str,
        request: PrizeSettings,
        conn=Depends(get_db_connection)
):
    """Set prizes for a lottery event"""
    result = await LotteryBusiness.set_prizes(conn, event_id, request.prizes)
    return to_json_response(ListResponse(results=result))


@router.get("/events/{event_id}/prizes", response_model=SingleResponse[PrizeList],
            responses={404: {'model': ExceptionResponse}})
async def get_prizes(
        event_id: str,
        conn=Depends(get_db_connection)
):
    """Get prizes for a lottery event"""
    result = await LotteryBusiness.get_prizes(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.put("/prizes/{prize_id}", response_model=SingleResponse[Prize], responses={404: {'model': ExceptionResponse}})
async def update_prize(
        prize_id: int,
        request: PrizeUpdate,
        conn=Depends(get_db_connection)
):
    """Update a prize"""
    result = await LotteryBusiness.update_prize(conn, prize_id, request)
    return to_json_response(SingleResponse(result=result))


@router.delete("/prizes/{prize_id}", responses={404: {'model': ExceptionResponse}})
async def delete_prize(
        prize_id: int,
        conn=Depends(get_db_connection)
):
    """Delete a prize"""
    result = await LotteryBusiness.delete_prize(conn, prize_id)
    return to_json_response(SingleResponse(result=result))


@router.post("/draw/{event_id}", response_model=ListResponse[WinnersList],
             responses={
                 404: {'model': ExceptionResponse},
                 400: {'model': ExceptionResponse,
                       'description': 'Bad Request - Event already drawn or other parameter violation'}
             })
async def draw_winners(
        event_id=Path(),
        conn=Depends(get_db_connection)
):
    """Draw winners for a lottery event. An event can only be drawn once."""
    result = await LotteryBusiness.draw_winners(conn, event_id)
    return to_json_response(ListResponse(result=result))


@router.get("/events/{event_id}/winners", response_model=ListResponse[WinnersList],
            responses={404: {'model': ExceptionResponse}})
async def get_winners(
        event_id: str,
        conn=Depends(get_db_connection)
):
    """Get winners for a lottery event"""
    result = await LotteryBusiness.get_winners(conn, event_id)
    return to_json_response(ListResponse(result=result))


@router.delete("/events/{event_id}/winners", response_model=SingleResponse[ResetDrawingResponse],
               responses={
                   404: {'model': ExceptionResponse},
                   400: {'model': ExceptionResponse,
                         'description': 'Bad Request - Event has no winners or other parameter violation'}
               })
async def reset_drawing(
        event_id: str = Path(),
        conn=Depends(get_db_connection)
):
    """Reset a lottery drawing by deleting all winners and setting event status back to pending, allowing re-drawing"""
    result = await LotteryBusiness.reset_drawing(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.get("/events/{event_id}/export", response_model=SingleResponse[ExportWinnersResponse],
            responses={404: {'model': ExceptionResponse}})
async def export_winners(
        event_id: str,
        conn=Depends(get_db_connection)
):
    """Export winners for a lottery event to Excel"""
    result = await LotteryBusiness.export_winners(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.get("/export/{filename}")
async def download_export(filename: str):
    """Download an exported winners file"""
    file_path = os.path.join("exports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    return FileResponse(file_path, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.delete("/participants/{participant_id}", response_model=SingleResponse[DeleteParticipantResponse],
               responses={
                   404: {'model': ExceptionResponse},
                   400: {'model': ExceptionResponse, 'description': 'Bad Request - Event already drawn or other parameter violation'}
               })
async def delete_participant(
        participant_id: int = Path(),
        conn=Depends(get_db_connection)
):
    """Delete a specific participant. Cannot delete participants from events that have already been drawn."""
    result = await LotteryBusiness.delete_participant(conn, participant_id)
    return to_json_response(SingleResponse(result=result))


@router.delete("/events/{event_id}/participants", response_model=SingleResponse[DeleteAllParticipantsResponse],
               responses={
                   404: {'model': ExceptionResponse},
                   400: {'model': ExceptionResponse, 'description': 'Bad Request - Event already drawn or other parameter violation'}
               })
async def delete_all_participants(
        event_id: str = Path(),
        conn=Depends(get_db_connection)
):
    """Delete all participants for an event. Cannot delete participants from events that have already been drawn."""
    result = await LotteryBusiness.delete_all_participants(conn, event_id)
    return to_json_response(SingleResponse(result=result))
