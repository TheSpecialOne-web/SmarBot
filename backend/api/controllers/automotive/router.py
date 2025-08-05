"""Automotive diagnostic API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from api.domain.models.automotive.models import (
    DiagnosticArticle,
    DiagnosticSession,
    OBDCode,
    ServiceGarage,
    Vehicle,
    VehicleMake,
)
from api.infrastructures.llm.aws_bedrock.client import BedrockClient
from api.infrastructures.llm.bedrock_automotive_service import BedrockLLMService
from api.infrastructures.opensearch.opensearch_service import OpenSearchService
from api.services.automotive.csv_ingestion_service import AutomotiveCSVIngestionService


# Request/Response models
class OBDCodeAnalysisRequest(BaseModel):
    """Request for OBD code analysis."""
    obd_code: str
    vehicle_make: Optional[VehicleMake] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None


class DiagnosticSearchRequest(BaseModel):
    """Request for diagnostic search."""
    query: str
    vehicle_make: Optional[VehicleMake] = None
    obd_codes: Optional[List[str]] = None
    limit: int = 10


class ChatRequest(BaseModel):
    """Request for automotive chat."""
    message: str
    session_id: Optional[UUID] = None
    context_articles: Optional[List[str]] = None


class CSVIngestionResponse(BaseModel):
    """Response for CSV ingestion."""
    success_count: int
    error_count: int
    total_processed: int


# Initialize services
def get_bedrock_client() -> BedrockClient:
    """Get Bedrock client dependency."""
    return BedrockClient()


def get_opensearch_service() -> OpenSearchService:
    """Get OpenSearch service dependency."""
    return OpenSearchService()


def get_bedrock_llm_service(
    bedrock_client: BedrockClient = Depends(get_bedrock_client)
) -> BedrockLLMService:
    """Get Bedrock LLM service dependency."""
    return BedrockLLMService(bedrock_client)


def get_csv_ingestion_service(
    bedrock_client: BedrockClient = Depends(get_bedrock_client),
    opensearch_service: OpenSearchService = Depends(get_opensearch_service)
) -> AutomotiveCSVIngestionService:
    """Get CSV ingestion service dependency."""
    return AutomotiveCSVIngestionService(bedrock_client, opensearch_service)


# Router
automotive_router = APIRouter(prefix="/automotive", tags=["automotive"])


@automotive_router.post("/analyze-obd-code")
async def analyze_obd_code(
    request: OBDCodeAnalysisRequest,
    llm_service: BedrockLLMService = Depends(get_bedrock_llm_service)
) -> dict:
    """Analyze an OBD diagnostic code."""
    try:
        vehicle = None
        if request.vehicle_make and request.vehicle_model and request.vehicle_year:
            vehicle = Vehicle(
                make=request.vehicle_make,
                model=request.vehicle_model,
                year=request.vehicle_year
            )
        
        analysis = llm_service.analyze_obd_code(request.obd_code, vehicle)
        
        return {
            "obd_code": request.obd_code,
            "analysis": analysis,
            "vehicle": vehicle.model_dump() if vehicle else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@automotive_router.post("/search-diagnostics")
async def search_diagnostics(
    request: DiagnosticSearchRequest,
    opensearch_service: OpenSearchService = Depends(get_opensearch_service),
    bedrock_client: BedrockClient = Depends(get_bedrock_client)
) -> dict:
    """Search automotive diagnostic articles."""
    try:
        # Generate embeddings for the query
        embeddings = bedrock_client.create_embeddings(request.query)
        
        # Prepare filters
        filters = {}
        if request.vehicle_make:
            filters["vehicle_info.make"] = request.vehicle_make.value
        
        # Search documents
        results = opensearch_service.search_documents(
            index_name="goo_net_diagnostics",
            query=request.query,
            filters=filters,
            vector=embeddings,
            size=request.limit
        )
        
        # Process results
        articles = []
        for hit in results.get("hits", {}).get("hits", []):
            source = hit["_source"]
            articles.append({
                "article_id": source.get("article_id"),
                "summary": source.get("summary"),
                "obd_codes": source.get("obd_codes", []),
                "vehicle_info": source.get("vehicle_info"),
                "diagnostic_category": source.get("diagnostic_category"),
                "score": hit["_score"]
            })
        
        return {
            "query": request.query,
            "total": results.get("hits", {}).get("total", {}).get("value", 0),
            "articles": articles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@automotive_router.get("/search-obd-codes/{obd_code}")
async def search_obd_codes(
    obd_code: str,
    opensearch_service: OpenSearchService = Depends(get_opensearch_service)
) -> dict:
    """Search for specific OBD diagnostic codes."""
    try:
        results = opensearch_service.search_obd_codes("goo_net_diagnostics", obd_code)
        
        articles = []
        for hit in results.get("hits", {}).get("hits", []):
            source = hit["_source"]
            articles.append({
                "article_id": source.get("article_id"),
                "text": source.get("text", "")[:200] + "...",
                "summary": source.get("summary"),
                "vehicle_info": source.get("vehicle_info"),
                "highlights": hit.get("highlight", {})
            })
        
        return {
            "obd_code": obd_code,
            "total": results.get("hits", {}).get("total", {}).get("value", 0),
            "articles": articles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OBD search failed: {str(e)}")


@automotive_router.post("/chat")
async def automotive_chat(
    request: ChatRequest,
    llm_service: BedrockLLMService = Depends(get_bedrock_llm_service),
    opensearch_service: OpenSearchService = Depends(get_opensearch_service)
) -> dict:
    """Chat with automotive AI assistant."""
    try:
        # Get context articles if provided
        context_articles = []
        if request.context_articles:
            # In a real implementation, you would fetch these articles
            # For now, we'll create empty placeholders
            pass
        
        # Generate response
        response_parts = []
        for chunk in llm_service.generate_automotive_chat_response(
            request.message, 
            context_articles
        ):
            response_parts.append(chunk)
        
        response = "".join(response_parts)
        
        return {
            "message": request.message,
            "response": response,
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@automotive_router.post("/ingest-csv")
async def ingest_csv_data(
    file: UploadFile = File(...),
    ingestion_service: AutomotiveCSVIngestionService = Depends(get_csv_ingestion_service)
) -> CSVIngestionResponse:
    """Ingest automotive diagnostic data from CSV file."""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Process CSV
        success_count, error_count = ingestion_service.ingest_csv_data(csv_content)
        total_processed = success_count + error_count
        
        return CSVIngestionResponse(
            success_count=success_count,
            error_count=error_count,
            total_processed=total_processed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV ingestion failed: {str(e)}")


@automotive_router.get("/vehicle-makes")
async def get_vehicle_makes() -> dict:
    """Get list of supported vehicle makes."""
    return {
        "makes": [make.value for make in VehicleMake]
    }


@automotive_router.get("/health")
async def health_check(
    opensearch_service: OpenSearchService = Depends(get_opensearch_service)
) -> dict:
    """Health check for automotive services."""
    try:
        # Check OpenSearch connection
        stats = opensearch_service.get_index_stats("goo_net_diagnostics")
        opensearch_status = "healthy"
    except:
        opensearch_status = "unhealthy"
    
    return {
        "status": "healthy",
        "opensearch": opensearch_status,
        "features": [
            "OBD Code Analysis",
            "Diagnostic Search", 
            "Automotive Chat",
            "CSV Data Ingestion"
        ]
    }