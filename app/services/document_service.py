from typing import Dict, Any, Optional
import datetime
from app.services.claude_service import ClaudeService
from app.db.models import Document, Case
from sqlalchemy.orm import Session

class DocumentService:
    def __init__(self):
        self.claude_service = ClaudeService()
    
    async def create_document(
        self, 
        db: Session,
        case_id: int,
        doc_type: str,
        recipient_info: Optional[Dict[str, Any]] = None
    ) -> Document:
        """사례 정보를 바탕으로 문서 초안 생성 및 저장"""
        
        # 사례 정보 조회
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError(f"Case with ID {case_id} not found")
        
        # 사례 정보 딕셔너리 구성
        case_info = {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "legal_category": case.category,
            "status": case.status
        }
        
        # Claude API를 통한 문서 초안 생성
        document_content = await self.claude_service.generate_document_draft(
            doc_type=doc_type,
            case_info=case_info,
            recipient_info=recipient_info
        )
        
        # 문서 제목 생성
        document_title = f"{doc_type} - {case.title} ({datetime.datetime.now().strftime('%Y-%m-%d')})"
        
        # 문서 DB 저장
        new_document = Document(
            title=document_title,
            content=document_content,
            doc_type=doc_type,
            case_id=case_id
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        
        return new_document
    
    def format_document_for_download(self, document: Document, format_type: str = "txt") -> Dict[str, Any]:
        """문서를 다운로드 가능한 형식으로 포맷팅"""
        
        # 기본 텍스트 형식
        if format_type == "txt":
            content = document.content
            filename = f"{document.title.replace(' ', '_')}.txt"
            mime_type = "text/plain"
        
        # HTML 형식 (필요에 따라 스타일링 추가)
        elif format_type == "html":
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{document.title}</title>
                <style>
                    body {{ font-family: 'Malgun Gothic', sans-serif; margin: 2cm; }}
                    h1 {{ text-align: center; }}
                    .date {{ text-align: right; margin-bottom: 2em; }}
                    .content {{ line-height: 1.6; }}
                    .footer {{ margin-top: 2em; text-align: right; }}
                </style>
            </head>
            <body>
                <h1>{document.title}</h1>
                <div class="date">{datetime.datetime.now().strftime('%Y년 %m월 %d일')}</div>
                <div class="content">{document.content.replace('\n', '<br>')}</div>
            </body>
            </html>
            """
            content = html_template
            filename = f"{document.title.replace(' ', '_')}.html"
            mime_type = "text/html"
            
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
            
        return {
            "content": content,
            "filename": filename,
            "mime_type": mime_type
        }