from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, ConfigDict
from enum import Enum


class LotteryEventType(str, Enum):
    """Enum for lottery event types"""
    GENERAL = "general"
    FINAL_TEACHING = "final_teaching"


class LotteryEventBase(BaseModel):
    academic_year_term: str
    name: str
    description: str
    event_date: datetime
    type: LotteryEventType = LotteryEventType.GENERAL


class LotteryEventCreate(LotteryEventBase):
    pass


class LotteryEvent(LotteryEventBase):
    id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentBase(BaseModel):
    """Base model for student data - removed personal information"""
    id: str
    department: Optional[str] = None
    name: Optional[str] = None
    grade: Optional[str] = None


class TeachingCommentBase(BaseModel):
    """Base model for teaching comments"""
    required_surveys: Optional[int] = None
    completed_surveys: Optional[int] = None
    surveys_completed: Optional[bool] = None
    valid_surveys: Optional[bool] = None


class StudentImport(StudentBase, TeachingCommentBase):
    """Model for importing students with optional teaching comment data"""
    pass


class StudentsImport(BaseModel):
    """Batch import multiple students"""
    students: List[StudentImport]


class ParticipantBase(BaseModel):
    """Base model for participants with student data"""
    student_id: str
    event_id: str

class Participant(ParticipantBase):
    # Participant fields
    id: int
    department: Optional[str] = None
    name: Optional[str] = None
    grade: Optional[str] = None
    created_at: datetime


class FinalParticipant(Participant):
    """Full participant model with all related data"""
    # Teaching comments fields
    required_surveys: Optional[int] = None
    completed_surveys: Optional[int] = None
    surveys_completed: Optional[bool] = None
    valid_surveys: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ParticipantList(BaseModel):
    total: int
    participants: List[Participant]

class FinalParticipantList(BaseModel):
    total: int
    participants: List[FinalParticipant]


class PrizeBase(BaseModel):
    name: str
    quantity: int


class PrizeCreate(PrizeBase):
    pass


class Prize(PrizeBase):
    id: int
    event_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PrizeUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None


class PrizeList(BaseModel):
    prizes: List[Prize]


class PrizeSettings(BaseModel):
    prizes: List[PrizeCreate]


class Winner(BaseModel):
    id: int
    event_id: str
    prize_id: int
    participant_id: int
    prize_name: str
    created_at: datetime
    # Student fields - removed personal information
    student_id: str 
    department: Optional[str] = None
    name: Optional[str] = None
    grade: Optional[str] = None
    # Teaching comments fields
    required_surveys: Optional[int] = None
    completed_surveys: Optional[int] = None
    surveys_completed: Optional[bool] = None
    valid_surveys: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class WinnersByPrize(BaseModel):
    prize_name: str
    quantity: int
    winners: List[Dict[str, Any]]


class WinnersList(BaseModel):
    prizes: List[WinnersByPrize]


class DrawRequest(BaseModel):
    event_id: str
    

class ExportWinnersResponse(BaseModel):
    file_url: str

class ResetDrawingResponse(BaseModel):
    event_id: str
    deleted_winners_count: int
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class DeleteParticipantResponse(BaseModel):
    participant_id: int
    event_id: str
    message: str


class DeleteAllParticipantsResponse(BaseModel):
    event_id: str
    deleted_participants_count: int
    message: str


class ImportedStudent(BaseModel):
    """Model for successfully imported student"""
    participant_id: int
    student_id: str
    student_name: str


class SkippedStudent(BaseModel):
    """Model for skipped student with reason"""
    student_id: str
    reason: str


class ImportStudentsResponse(BaseModel):
    """Response model for student import operation"""
    imported: List[ImportedStudent]
    skipped: List[SkippedStudent]
    total_imported: int
    total_skipped: int
 