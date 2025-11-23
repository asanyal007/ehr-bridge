"""
Pydantic models for the AI Data Interoperability Platform
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class JobStatus(str, Enum):
    """Enumeration of possible job statuses"""
    DRAFT = "DRAFT"
    ANALYZING = "ANALYZING"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ERROR = "ERROR"


class TransformationType(str, Enum):
    """Types of field transformations"""
    DIRECT = "DIRECT"
    CONCAT = "CONCAT"
    SPLIT = "SPLIT"
    FORMAT_DATE = "FORMAT_DATE"
    UPPERCASE = "UPPERCASE"
    LOWERCASE = "LOWERCASE"
    TRIM = "TRIM"
    CUSTOM = "CUSTOM"


class FieldMapping(BaseModel):
    """Represents a single field mapping suggestion"""
    sourceField: str
    targetField: str
    confidenceScore: float = Field(ge=0.0, le=1.0)
    suggestedTransform: TransformationType
    transformParams: Optional[Dict[str, Any]] = None
    isApproved: bool = False
    isRejected: bool = False
    # GPT-OSS enhanced fields (optional)
    gpt_oss_reasoning: Optional[str] = None
    gpt_oss_clinical_context: Optional[str] = None
    gpt_oss_type_compatible: Optional[bool] = None
    # Low confidence suggestion (<40% confidence)
    low_confidence_suggestion: Optional[Dict[str, Any]] = None


class CreateJobRequest(BaseModel):
    """Request model for creating a new job"""
    sourceSchema: Dict[str, str]
    targetSchema: Dict[str, str]
    userId: str


class AnalyzeJobRequest(BaseModel):
    """Request model for analyzing schemas"""
    userId: str


class ApproveJobRequest(BaseModel):
    """Request model for approving mappings"""
    finalMappings: List[FieldMapping]
    userId: str


class MappingJob(BaseModel):
    """Complete mapping job model"""
    jobId: str
    sourceSchema: Dict[str, str]
    targetSchema: Dict[str, str]
    suggestedMappings: List[FieldMapping] = []
    finalMappings: List[FieldMapping] = []
    status: JobStatus
    userId: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class DataProfile(BaseModel):
    """Statistical profile of a data column"""
    fieldName: str
    dataType: str
    sampleValues: List[Any]
    nullCount: int
    uniqueCount: int
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None


class TransformRequest(BaseModel):
    """Request model for testing transformations"""
    mappings: List[FieldMapping]
    sampleData: List[Dict[str, Any]]


# ============================
# Terminology Normalization
# ============================

class TerminologyCandidate(BaseModel):
    """A single normalization candidate for a source value"""
    sourceValue: str
    normalized: str
    confidence: float
    source: str = Field(default="ai", description="ai|cache|static")
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class TerminologySuggestion(BaseModel):
    """Suggestions for a specific field/path"""
    fieldPath: str
    suggestedSystem: Optional[str] = None
    strategy: str = Field(default="hybrid")
    sourceDistincts: List[Dict[str, Any]] = []  # {value, count}
    candidates: List[TerminologyCandidate] = []


class TerminologyNormalization(BaseModel):
    """Approved normalization mapping for a field"""
    jobId: str
    fieldPath: str
    strategy: str = "hybrid"
    system: Optional[str] = None
    mapping: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="sourceValue -> { normalized, system?, code?, display? }",
    )
    approvedBy: Optional[str] = None


class TerminologyNormalizeRequest(BaseModel):
    """Request to generate terminology suggestions"""
    sampleData: Optional[List[Dict[str, Any]]] = None
    sampleSize: int = 500


class TerminologyNormalizeResponse(BaseModel):
    """Response with terminology suggestions"""
    jobId: str
    suggestions: List[TerminologySuggestion]

