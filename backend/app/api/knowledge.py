"""知识库管理API。"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.core.rag import rag_engine
from app.db.models import KnowledgeDocumentRecord
from app.models.schemas import (
    KnowledgeDocCreate,
    KnowledgeDocSchema,
    KnowledgeDocUpdate,
    KnowledgeTestRequest,
    KnowledgeTestResponse,
)
from app.services.document_parser import parse_document
from app.services.persistence import (
    delete_knowledge_record,
    get_knowledge_record,
    list_knowledge_records,
    save_knowledge_record,
)

router = APIRouter(prefix="/admin/knowledge")
logger = logging.getLogger(__name__)


def _to_schema(record: KnowledgeDocumentRecord) -> KnowledgeDocSchema:
    return KnowledgeDocSchema(
        id=record.id,
        title=record.title,
        category=record.category,
        content=record.content,
        file_path=record.file_path,
        upload_time=record.upload_time.strftime("%Y-%m-%d %H:%M"),
        status=record.status,
        kind=record.kind,
        source=record.source,
        keywords=record.keywords,
        tags=record.tags,
    )


@router.get("/list", response_model=list[KnowledgeDocSchema])
async def list_docs():
    return [_to_schema(record) for record in await list_knowledge_records()]


@router.post("/entries", response_model=KnowledgeDocSchema)
async def create_entry(payload: KnowledgeDocCreate):
    doc_id = str(uuid.uuid4())
    record = KnowledgeDocumentRecord(
        id=doc_id,
        title=payload.title,
        category=payload.category,
        content=payload.content,
        kind=payload.kind,
        source=payload.source or payload.title,
        keywords=payload.keywords,
        tags=payload.tags,
        status="active",
    )
    return _to_schema(await save_knowledge_record(record))


@router.put("/{doc_id}", response_model=KnowledgeDocSchema)
async def update_entry(doc_id: str, payload: KnowledgeDocUpdate):
    existing = await get_knowledge_record(doc_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    record = KnowledgeDocumentRecord(
        id=doc_id,
        title=payload.title,
        category=payload.category,
        content=payload.content,
        kind=payload.kind,
        source=payload.source or payload.title,
        file_path=existing.file_path,
        keywords=payload.keywords,
        tags=payload.tags,
        status=payload.status,
        upload_time=existing.upload_time,
        updated_at=datetime.now(),
    )
    return _to_schema(await save_knowledge_record(record))


@router.post("/upload", response_model=KnowledgeDocSchema)
async def upload_doc(
    file: UploadFile = File(...),
    category: str = Form("待分类"),
):
    content = await file.read()
    filename = Path(file.filename or "untitled.txt").name
    try:
        text_content = parse_document(filename, content)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    upload_dir = Path(settings.knowledge_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}{Path(filename).suffix.lower()}"
    file_path = upload_dir / stored_filename
    file_path.write_bytes(content)

    record = KnowledgeDocumentRecord(
        id=str(uuid.uuid4()),
        title=Path(filename).stem,
        category=category,
        content=text_content,
        kind="document",
        source=filename,
        file_path=str(file_path),
        keywords=[],
        tags=[],
        status="active",
    )
    try:
        return _to_schema(await save_knowledge_record(record))
    except Exception:
        file_path.unlink(missing_ok=True)
        raise


@router.delete("/{doc_id}")
async def delete_doc(doc_id: str):
    existing = await get_knowledge_record(doc_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    if not await delete_knowledge_record(doc_id):
        raise HTTPException(status_code=404, detail="知识条目不存在")
    if existing.file_path:
        try:
            Path(existing.file_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("无法删除知识库原始文件: %s", existing.file_path)
    return {"status": "ok"}


@router.post("/test", response_model=KnowledgeTestResponse)
async def test_knowledge(req: KnowledgeTestRequest):
    result = rag_engine.retrieve_with_sources(req.question)
    if result.found:
        return KnowledgeTestResponse(
            answer=result.answer,
            sources=[item.source for item in result.evidence],
            confidence=result.confidence,
            evidence=[
                {
                    "title": item.title,
                    "category": item.category,
                    "score": item.score,
                    "source": item.source,
                    "excerpt": item.content[:160],
                }
                for item in result.evidence
            ],
        )
    return KnowledgeTestResponse(
        answer="抱歉，知识库中暂无足够相关的证据。建议补充相关文档。",
        sources=[],
        confidence=0.0,
    )
