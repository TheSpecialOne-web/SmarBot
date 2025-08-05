"""CSV ingestion service for automotive OBD diagnostic data."""

import ast
import csv
import re
from datetime import datetime
from io import StringIO
from typing import List, Optional, Tuple

import pandas as pd

from api.domain.models.automotive.models import (
    DiagnosticArticle,
    OBDCode,
    OBDCodeType,
    Vehicle,
    VehicleMake,
)
from api.infrastructures.llm.aws_bedrock.client import BedrockClient
from api.infrastructures.opensearch.opensearch_service import OpenSearchService


class AutomotiveCSVIngestionService:
    """Service for ingesting automotive diagnostic data from CSV files."""
    
    def __init__(self, bedrock_client: BedrockClient, opensearch_service: OpenSearchService):
        """Initialize the ingestion service."""
        self.bedrock_client = bedrock_client
        self.opensearch_service = opensearch_service
        self.index_name = "goo_net_diagnostics"
    
    def ingest_csv_data(self, csv_content: str) -> Tuple[int, int]:
        """
        Ingest CSV data and return (success_count, error_count).
        
        Expected CSV format:
        article_id,create_time,category_id,text,summary,article_length,sentence_scores
        """
        try:
            # Ensure the index exists
            self.opensearch_service.create_automotive_index(self.index_name)
            
            # Parse CSV
            df = pd.read_csv(StringIO(csv_content))
            
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    article = self._parse_csv_row(row)
                    if article:
                        # Create embeddings for the text
                        embeddings = self.bedrock_client.create_embeddings(
                            article.text[:2000]  # Limit text length for embeddings
                        )
                        
                        # Prepare document for indexing
                        doc = self._prepare_document_for_indexing(article, embeddings)
                        
                        # Index the document
                        if self.opensearch_service.index_document(
                            self.index_name, 
                            article.article_id, 
                            doc
                        ):
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"Error processing row: {e}")
                    error_count += 1
            
            return success_count, error_count
            
        except Exception as e:
            raise Exception(f"CSV ingestion failed: {e}")
    
    def _parse_csv_row(self, row: pd.Series) -> Optional[DiagnosticArticle]:
        """Parse a single CSV row into a DiagnosticArticle."""
        try:
            # Parse sentence scores
            sentence_scores = []
            if pd.notna(row.get('sentence_scores')):
                try:
                    scores_str = str(row['sentence_scores']).strip()
                    sentence_scores = ast.literal_eval(scores_str)
                except (ValueError, SyntaxError):
                    sentence_scores = []
            
            # Extract OBD codes from text
            obd_codes = self._extract_obd_codes(str(row['text']))
            
            # Extract vehicle information
            vehicle = self._extract_vehicle_info(str(row['text']))
            
            # Parse create_time
            create_time = datetime.now()
            if pd.notna(row.get('create_time')):
                try:
                    create_time = pd.to_datetime(row['create_time'])
                except:
                    pass
            
            # Create article
            article = DiagnosticArticle(
                article_id=str(row['article_id']),
                create_time=create_time,
                category_id=str(row.get('category_id', '')),
                text=str(row['text']),
                summary=str(row.get('summary', '')),
                article_length=int(row.get('article_length', 0)),
                sentence_scores=sentence_scores,
                obd_codes=obd_codes,
                vehicle=vehicle,
                diagnostic_category=self._categorize_diagnostic(str(row['text'])),
                repair_difficulty=self._assess_difficulty(str(row['text'])),
                estimated_time=self._estimate_repair_time(str(row['text'])),
                required_tools=self._extract_tools(str(row['text']))
            )
            
            return article
            
        except Exception as e:
            print(f"Error parsing CSV row: {e}")
            return None
    
    def _extract_obd_codes(self, text: str) -> List[OBDCode]:
        """Extract OBD diagnostic codes from text."""
        obd_codes = []
        
        # Common OBD code patterns
        patterns = [
            r'[PCBU]\d{4}[-]?\w*',  # Standard OBD codes
            r'[PCBU]\d{3}[-]?\d+[A-Z]*',  # Alternative formats
            r'[UPC]\d{4}[-]?\d*[A-Z]*',  # Japanese specific patterns
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                code = match.upper()
                code_type = self._determine_code_type(code)
                severity = self._assess_code_severity(code, text)
                description = self._extract_code_description(code, text)
                
                obd_code = OBDCode(
                    code=code,
                    description=description,
                    code_type=code_type,
                    severity=severity
                )
                obd_codes.append(obd_code)
        
        return obd_codes
    
    def _extract_vehicle_info(self, text: str) -> Optional[Vehicle]:
        """Extract vehicle information from diagnostic text."""
        # Japanese vehicle make patterns
        make_patterns = {
            VehicleMake.HONDA: [r'ホンダ', r'Honda', r'Ｎ－ＢＯＸ', r'N-BOX', r'フィット'],
            VehicleMake.TOYOTA: [r'トヨタ', r'Toyota', r'プリウス', r'カローラ'],
            VehicleMake.NISSAN: [r'ニッサン', r'Nissan', r'日産', r'セレナ', r'ノート'],
            VehicleMake.MAZDA: [r'マツダ', r'Mazda', r'デミオ', r'アクセラ'],
            VehicleMake.SUBARU: [r'スバル', r'Subaru', r'インプレッサ', r'レガシィ'],
        }
        
        # Find vehicle make
        detected_make = None
        for make, patterns in make_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_make = make
                    break
            if detected_make:
                break
        
        if not detected_make:
            return None
        
        # Extract model and year
        model = self._extract_model(text, detected_make)
        year = self._extract_year(text)
        
        if model and year:
            return Vehicle(
                make=detected_make,
                model=model,
                year=year
            )
        
        return None
    
    def _determine_code_type(self, code: str) -> OBDCodeType:
        """Determine OBD code type from code prefix."""
        if code.startswith('P'):
            return OBDCodeType.POWERTRAIN
        elif code.startswith('C'):
            return OBDCodeType.CHASSIS
        elif code.startswith('B'):
            return OBDCodeType.BODY
        elif code.startswith('U'):
            return OBDCodeType.NETWORK
        else:
            return OBDCodeType.POWERTRAIN  # Default
    
    def _assess_code_severity(self, code: str, text: str) -> str:
        """Assess the severity of an OBD code based on context."""
        high_severity_keywords = ['危険', '重要', '緊急', '警告', '異常']
        medium_severity_keywords = ['注意', '確認', '点検']
        
        text_lower = text.lower()
        
        for keyword in high_severity_keywords:
            if keyword in text_lower:
                return "High"
        
        for keyword in medium_severity_keywords:
            if keyword in text_lower:
                return "Medium"
        
        return "Low"
    
    def _extract_code_description(self, code: str, text: str) -> str:
        """Extract description for an OBD code from context."""
        # Look for text near the code
        code_index = text.find(code)
        if code_index != -1:
            # Extract surrounding text
            start = max(0, code_index - 50)
            end = min(len(text), code_index + len(code) + 100)
            context = text[start:end]
            
            # Clean up the description
            description = context.replace(code, '').strip()
            return description[:200]  # Limit length
        
        return f"Diagnostic code {code}"
    
    def _extract_model(self, text: str, make: VehicleMake) -> Optional[str]:
        """Extract vehicle model from text."""
        if make == VehicleMake.HONDA:
            models = [r'Ｎ－ＢＯＸ', r'N-BOX', r'フィット', r'ヴェゼル']
        elif make == VehicleMake.TOYOTA:
            models = [r'プリウス', r'カローラ', r'ヴィッツ']
        else:
            models = []
        
        for model_pattern in models:
            match = re.search(model_pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        
        return "Unknown Model"
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract vehicle year from text."""
        # Look for year patterns (2000-2025)
        year_match = re.search(r'(20[0-2]\d)', text)
        if year_match:
            return int(year_match.group(1))
        
        # Look for Japanese year format
        year_match = re.search(r'(\d{4})年', text)
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _categorize_diagnostic(self, text: str) -> str:
        """Categorize the type of diagnostic."""
        if 'エンジン' in text or 'engine' in text.lower():
            return "Engine"
        elif 'ブレーキ' in text or 'brake' in text.lower():
            return "Brake System"
        elif 'パワーステアリング' in text or 'power steering' in text.lower():
            return "Power Steering"
        elif 'エアコン' in text or 'air conditioning' in text.lower():
            return "Air Conditioning"
        else:
            return "General"
    
    def _assess_difficulty(self, text: str) -> str:
        """Assess repair difficulty based on text content."""
        if any(word in text for word in ['専門', '特殊工具', '分解']):
            return "Expert"
        elif any(word in text for word in ['中級', '経験']):
            return "Intermediate"
        else:
            return "Basic"
    
    def _estimate_repair_time(self, text: str) -> str:
        """Estimate repair time from text."""
        if any(word in text for word in ['数日', '長時間']):
            return "4-8 hours"
        elif any(word in text for word in ['半日', '午後']):
            return "2-4 hours"
        else:
            return "1-2 hours"
    
    def _extract_tools(self, text: str) -> List[str]:
        """Extract required tools from text."""
        tools = []
        tool_patterns = [
            r'OBDスキャナー', r'テスター', r'工具', r'レンチ', r'ドライバー'
        ]
        
        for pattern in tool_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tools.append(pattern)
        
        return tools
    
    def _prepare_document_for_indexing(
        self, 
        article: DiagnosticArticle, 
        embeddings: List[float]
    ) -> dict:
        """Prepare document for OpenSearch indexing."""
        doc = {
            "id": article.article_id,
            "article_id": article.article_id,
            "create_time": article.create_time.isoformat(),
            "category_id": article.category_id,
            "text": article.text,
            "summary": article.summary,
            "article_length": article.article_length,
            "sentence_scores": article.sentence_scores,
            "content_vector": embeddings,
        }
        
        # Add OBD codes
        if article.obd_codes:
            doc["obd_codes"] = [
                {
                    "code": code.code,
                    "description": code.description,
                    "type": code.code_type.value,
                    "severity": code.severity
                }
                for code in article.obd_codes
            ]
        
        # Add vehicle info
        if article.vehicle:
            doc["vehicle_info"] = {
                "make": article.vehicle.make.value,
                "model": article.vehicle.model,
                "year": article.vehicle.year
            }
        
        # Add diagnostic metadata
        if article.diagnostic_category:
            doc["diagnostic_category"] = article.diagnostic_category
        if article.repair_difficulty:
            doc["repair_difficulty"] = article.repair_difficulty
        if article.estimated_time:
            doc["estimated_time"] = article.estimated_time
        if article.required_tools:
            doc["required_tools"] = article.required_tools
        
        return doc