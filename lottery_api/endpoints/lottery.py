import os
from typing import List, Optional, Union
from urllib.parse import quote
from fastapi import APIRouter, Depends, status, File, UploadFile, Query, HTTPException, Path
from fastapi.responses import FileResponse
from lottery_api.data_access_object.db import get_db_connection
from lottery_api.business_model.lottery_business import LotteryBusiness
from lottery_api.lib.auth_library.permission import depend_auth, Auth
from lottery_api.lib.response import ExceptionResponse, SingleResponse, ListResponse, to_json_response
from lottery_api.schema.lottery import (
    LotteryEventCreate, LotteryEvent, LotteryEventType, LotteryEventUpdate,
    StudentImport, StudentsImport, FinalTeachingStudentsImport, ParticipantList,
    PrizeCreate, PrizeSettings, PrizeList, Prize, PrizeUpdate,
    DrawRequest, WinnersList, ExportWinnersResponse, FinalParticipantList, ResetDrawingResponse,
    DeleteParticipantResponse, DeleteAllParticipantsResponse, ImportStudentsResponse,
    SoftDeleteEventResponse
)

router = APIRouter(prefix="/lottery", tags=["lottery"])


@router.post("/events", response_model=SingleResponse[LotteryEvent], status_code=status.HTTP_201_CREATED)
async def create_lottery_event(
        request: LotteryEventCreate,
        auth: Auth = depend_auth(),
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
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Get all lottery events with pagination"""
    result = await LotteryBusiness.get_lottery_events(conn, limit, offset, event_type.value if event_type else None)
    return to_json_response(ListResponse(result=result))


@router.get("/events/{event_id}", response_model=SingleResponse[LotteryEvent],
            responses={404: {'model': ExceptionResponse}})
async def get_lottery_event(
        event_id: str,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Get a lottery event by ID"""
    result = await LotteryBusiness.get_lottery_event(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.put("/events/{event_id}", response_model=SingleResponse[LotteryEvent],
           responses={
               404: {'model': ExceptionResponse},
               400: {'model': ExceptionResponse, 'description': 'Bad Request - Cannot update drawn events'}
           })
async def update_lottery_event(
        event_id: str,
        request: LotteryEventUpdate,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Update a lottery event. Cannot update events that have already been drawn."""
    result = await LotteryBusiness.update_lottery_event(conn, event_id, request)
    return to_json_response(SingleResponse(result=result))


@router.post("/events/{event_id}/participants", response_model=SingleResponse[ImportStudentsResponse], 
             status_code=status.HTTP_201_CREATED,
             responses={404: {'model': ExceptionResponse}})
async def import_students_and_add_participants(
        event_id: str,
        request: Union[StudentsImport, FinalTeachingStudentsImport],
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Import students and add them as participants to a lottery event.
    
    For general events: Use StudentsImport format - Oracle database will be queried for additional student info.
    For final_teaching events: Use FinalTeachingStudentsImport format - Complete student info should be provided.
    """
    result = await LotteryBusiness.import_students_and_add_participants(
        conn, event_id, [student.dict() for student in request.students]
    )
    return to_json_response(SingleResponse(result=result))


@router.get("/events/{event_id}/participants", response_model=SingleResponse[ParticipantList],
            responses={404: {'model': ExceptionResponse}})
async def get_participants(
        event_id: str,
        limit: int = Query(1000, ge=1, le=10000),
        offset: int = Query(0, ge=0),
        auth: Auth = depend_auth(),
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
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Set prizes for a lottery event"""
    result = await LotteryBusiness.set_prizes(conn, event_id, request.prizes)
    return to_json_response(ListResponse(result=result))


@router.get("/events/{event_id}/prizes", response_model=SingleResponse[PrizeList],
            responses={404: {'model': ExceptionResponse}})
async def get_prizes(
        event_id: str,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Get prizes for a lottery event"""
    result = await LotteryBusiness.get_prizes(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.put("/prizes/{prize_id}", response_model=SingleResponse[Prize], responses={404: {'model': ExceptionResponse}})
async def update_prize(
        prize_id: int,
        request: PrizeUpdate,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Update a prize"""
    result = await LotteryBusiness.update_prize(conn, prize_id, request)
    return to_json_response(SingleResponse(result=result))


@router.delete("/prizes/{prize_id}", responses={404: {'model': ExceptionResponse}})
async def delete_prize(
        prize_id: int,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Delete a prize"""
    result = await LotteryBusiness.delete_prize(conn, prize_id)
    return to_json_response(SingleResponse(result=result))


@router.post("/events/{event_id}/draw", response_model=ListResponse[WinnersList],
             responses={
                 404: {'model': ExceptionResponse},
                 400: {'model': ExceptionResponse,
                       'description': 'Bad Request - Event already drawn or other parameter violation'}
             })
async def draw_winners(
        event_id: str = Path(),
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Draw winners for a lottery event. An event can only be drawn once."""
    result = await LotteryBusiness.draw_winners(conn, event_id)
    return to_json_response(ListResponse(result=result))


@router.get("/events/{event_id}/winners", response_model=ListResponse[WinnersList],
            responses={404: {'model': ExceptionResponse}})
async def get_winners(
        event_id: str,
        auth: Auth = depend_auth(),
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
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Reset a lottery drawing by deleting all winners and setting event status back to pending, allowing re-drawing"""
    result = await LotteryBusiness.reset_drawing(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.get("/events/{event_id}/winners/export",
            responses={404: {'model': ExceptionResponse}})
async def export_winners(
        event_id: str,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Export winners for a lottery event to Excel and return the file directly"""
    result = await LotteryBusiness.export_winners(conn, event_id)
    # Extract filename from the file_url
    filename = result["file_url"].split("/")[-1]
    file_path = os.path.join("exports", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Extract just the filename without path for display
    display_filename = filename
    # If it's a complex filename with timestamp, extract just the meaningful part
    if "_" in display_filename:
        # Keep the original filename as is for Chinese support
        display_filename = filename
    
    # URL encode the filename to handle Chinese characters
    encoded_filename = quote(display_filename)
    
    return FileResponse(
        path=file_path,
        filename=display_filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/export/{filename}")
async def download_export(
        filename: str,
        auth: Auth = depend_auth()
):
    """Download an export file"""
    file_path = os.path.join("exports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # URL encode the filename to handle Chinese characters
    encoded_filename = quote(filename)
    
    return FileResponse(
        path=file_path, 
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.delete("/participants/{participant_id}", response_model=SingleResponse[DeleteParticipantResponse],
               responses={
                   404: {'model': ExceptionResponse},
                   400: {'model': ExceptionResponse, 'description': 'Bad Request - Event already drawn or other parameter violation'}
               })
async def delete_participant(
        participant_id: int = Path(),
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Delete a participant from a lottery event. Cannot delete from events that have already been drawn."""
    result = await LotteryBusiness.delete_participant(conn, participant_id)
    return to_json_response(SingleResponse(result=result))


@router.delete("/events/{event_id}/participants", response_model=SingleResponse[DeleteAllParticipantsResponse],
               responses={
                   404: {'model': ExceptionResponse},
                   400: {'model': ExceptionResponse, 'description': 'Bad Request - Event already drawn or other parameter violation'}
               })
async def delete_all_participants(
        event_id: str = Path(),
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Delete all participants from a lottery event. Cannot delete from events that have already been drawn."""
    result = await LotteryBusiness.delete_all_participants(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.delete("/events/{event_id}", response_model=SingleResponse[SoftDeleteEventResponse],
               responses={404: {'model': ExceptionResponse}})
async def soft_delete_event(
        event_id: str = Path(),
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """
    Soft delete a lottery event by setting deleted=true. 
    The event will be hidden from normal queries but data is preserved.
    """
    result = await LotteryBusiness.soft_delete_event(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.put("/events/{event_id}/restore", response_model=SingleResponse[SoftDeleteEventResponse],
           responses={404: {'model': ExceptionResponse}})
async def restore_event(
        event_id: str = Path(),
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """
    Restore a soft-deleted lottery event by setting deleted=false.
    The event will become visible in normal queries again.
    """
    result = await LotteryBusiness.restore_event(conn, event_id)
    return to_json_response(SingleResponse(result=result))


@router.get("/deleted-events", response_model=ListResponse[LotteryEvent])
async def get_deleted_events(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Get all soft-deleted lottery events with pagination"""
    result = await LotteryBusiness.get_deleted_events(conn, limit, offset)
    return to_json_response(ListResponse(result=result))
 