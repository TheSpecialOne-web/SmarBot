"""OBD diagnostic code models for automotive platform."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OBDCodeType(Enum):
    """OBD diagnostic code types."""
    POWERTRAIN = "P"  # Engine/transmission
    CHASSIS = "C"     # ABS, airbag, etc.
    BODY = "B"        # Body systems
    NETWORK = "U"     # Network/communication


class VehicleMake(Enum):
    """Japanese vehicle manufacturers."""
    HONDA = "Honda"
    TOYOTA = "Toyota"
    NISSAN = "Nissan"
    MAZDA = "Mazda"
    SUBARU = "Subaru"
    SUZUKI = "Suzuki"
    MITSUBISHI = "Mitsubishi"
    DAIHATSU = "Daihatsu"
    ISUZU = "Isuzu"


@dataclass
class OBDCode:
    """OBD diagnostic trouble code."""
    code: str  # e.g., "U3003-1C", "C1AE687"
    description: str
    code_type: OBDCodeType
    severity: str  # "Critical", "High", "Medium", "Low"
    
    def __post_init__(self):
        """Validate OBD code format."""
        if not self.code or len(self.code) < 4:
            raise ValueError("Invalid OBD code format")


@dataclass
class Vehicle:
    """Vehicle information."""
    make: VehicleMake
    model: str
    year: int
    engine_type: Optional[str] = None
    transmission: Optional[str] = None
    
    def __post_init__(self):
        """Validate vehicle data."""
        if self.year < 1996 or self.year > datetime.now().year + 1:
            raise ValueError("Invalid vehicle year")


class DiagnosticArticle(BaseModel):
    """Automotive diagnostic article from Goo-net Pit data."""
    
    article_id: str = Field(..., description="Unique article identifier")
    create_time: datetime = Field(..., description="Article creation timestamp")
    category_id: str = Field(..., description="Article category")
    text: str = Field(..., description="Full diagnostic text content")
    summary: str = Field(..., description="Article summary")
    article_length: int = Field(..., description="Character count of article")
    sentence_scores: List[List[float]] = Field(default_factory=list, description="Semantic scoring")
    
    # Automotive specific fields
    obd_codes: List[OBDCode] = Field(default_factory=list, description="Associated OBD codes")
    vehicle: Optional[Vehicle] = Field(None, description="Vehicle information")
    diagnostic_category: Optional[str] = Field(None, description="Diagnostic category")
    repair_difficulty: Optional[str] = Field(None, description="Repair complexity")
    estimated_time: Optional[str] = Field(None, description="Estimated repair time")
    required_tools: List[str] = Field(default_factory=list, description="Required tools")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            OBDCode: lambda v: {
                "code": v.code,
                "description": v.description,
                "type": v.code_type.value,
                "severity": v.severity
            },
            Vehicle: lambda v: {
                "make": v.make.value,
                "model": v.model,
                "year": v.year,
                "engine_type": v.engine_type,
                "transmission": v.transmission
            }
        }


class ServiceGarage(BaseModel):
    """Automotive service garage information."""
    
    garage_id: str = Field(..., description="Unique garage identifier")
    name: str = Field(..., description="Garage name")
    address: str = Field(..., description="Full address")
    latitude: float = Field(..., description="GPS latitude")
    longitude: float = Field(..., description="GPS longitude")
    phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Service capabilities
    specializations: List[str] = Field(default_factory=list, description="Service specializations")
    supported_makes: List[VehicleMake] = Field(default_factory=list, description="Supported vehicle makes")
    certification_level: Optional[str] = Field(None, description="Certification level")
    
    # Business information
    operating_hours: Optional[str] = Field(None, description="Business hours")
    rating: Optional[float] = Field(None, description="Customer rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class DiagnosticSession(BaseModel):
    """OBD diagnostic session."""
    
    session_id: UUID = Field(..., description="Unique session identifier")
    vehicle: Vehicle = Field(..., description="Vehicle being diagnosed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Session timestamp")
    
    # Diagnostic results
    detected_codes: List[OBDCode] = Field(default_factory=list, description="Detected OBD codes")
    related_articles: List[str] = Field(default_factory=list, description="Related article IDs")
    recommended_garages: List[str] = Field(default_factory=list, description="Recommended garage IDs")
    
    # Session metadata
    diagnostic_tool: Optional[str] = Field(None, description="OBD tool used")
    technician_notes: Optional[str] = Field(None, description="Technical notes")
    resolution_status: str = Field(default="open", description="Resolution status")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }