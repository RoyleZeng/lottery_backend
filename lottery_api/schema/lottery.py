from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, ConfigDict
from enum import Enum


class LotteryEventType(str, Enum):
    """Enum for lottery event types"""
    GENERAL = "general"
    FINAL_TEACHING = "final_teaching"


class ValidSurveys(str, Enum):
    """Enum for valid surveys status"""
    YES = "Y"  # 有效問卷
    NO = "N"   # 無效問卷


class SurveysCompleted(str, Enum):
    """Enum for surveys completed status"""
    YES = "Y"  # 已完成問卷
    NO = "N"   # 未完成問卷


class StudentType(str, Enum):
    """Enum for student type (corresponds to Oracle STUD_EXTRA)"""
    FOREIGN = "Y"  # 外籍生
    DOMESTIC = "N"  # 本國生


class LotteryEventBase(BaseModel):
    academic_year_term: str
    name: str
    description: str
    event_date: datetime
    type: LotteryEventType = LotteryEventType.GENERAL


class LotteryEventCreate(LotteryEventBase):
    pass


class LotteryEventUpdate(BaseModel):
    """Schema for updating lottery event - all fields are optional"""
    academic_year_term: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    type: Optional[LotteryEventType] = None


class LotteryEvent(LotteryEventBase):
    id: str
    status: str
    is_deleted: bool = False
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
    surveys_completed: Optional[SurveysCompleted] = None  # Y=已完成問卷, N=未完成問卷
    valid_surveys: Optional[ValidSurveys] = None  # Y=有效問卷, N=無效問卷


class FinalTeachingStudentImport(StudentBase, TeachingCommentBase):
    """Model for importing final_teaching students with complete information"""
    # 新增的完整個人資訊欄位
    id_number: Optional[str] = None  # 身份證字號
    address: Optional[str] = None    # 戶籍地址
    student_type: Optional[StudentType] = None  # 身份別：Y=外籍生, N=本國生
    phone: Optional[str] = None      # 手機
    email: Optional[str] = None      # 電子郵件


class StudentImport(StudentBase, TeachingCommentBase):
    """Model for importing students with optional teaching comment data"""
    pass


class StudentsImport(BaseModel):
    """Batch import multiple students"""
    students: List[StudentImport]


class FinalTeachingStudentsImport(BaseModel):
    """Batch import multiple final_teaching students with complete information"""
    students: List[FinalTeachingStudentImport]


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
    # Oracle fields (for general events, with privacy masking)
    oracle_student_id: Optional[str] = None
    chinese_name: Optional[str] = None
    english_name: Optional[str] = None
    # Final teaching complete data fields (for final_teaching events)
    id_number: Optional[str] = None
    address: Optional[str] = None
    student_type: Optional[StudentType] = None  # Y=外籍生, N=本國生
    phone: Optional[str] = None
    email: Optional[str] = None


class FinalParticipant(Participant):
    """Full participant model with all related data"""
    # Teaching comments fields
    required_surveys: Optional[int] = None
    completed_surveys: Optional[int] = None
    surveys_completed: Optional[SurveysCompleted] = None  # Y=已完成問卷, N=未完成問卷
    valid_surveys: Optional[ValidSurveys] = None  # Y=有效問卷, N=無效問卷

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
    surveys_completed: Optional[SurveysCompleted] = None  # Y=已完成問卷, N=未完成問卷
    valid_surveys: Optional[ValidSurveys] = None  # Y=有效問卷, N=無效問卷

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
    total_uploaded: int = 0  # 總共上傳的人數
    total_imported: int  # 匯入成功的人數（舊欄位，保持向後相容）
    total_eligible: int = 0  # 匯入成待抽名單中的人數
    total_skipped: int  # 跳過的人數
    inserted_count: int = 0  # 新增的參與者數量
    updated_count: int = 0   # 更新的參與者數量


class SoftDeleteEventResponse(BaseModel):
    """Response model for soft delete event operation"""
    event_id: str
    message: str
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)
 