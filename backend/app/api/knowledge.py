"""知识库管理API"""

import uuid
from datetime import datetime

from fastapi import APIRouter, File, UploadFile

from app.core.rag import rag_engine
from app.models.schemas import (
    KnowledgeDocSchema,
    KnowledgeTestRequest,
    KnowledgeTestResponse,
)

router = APIRouter(prefix="/admin/knowledge")

_docs_store: list[KnowledgeDocSchema] = [
    KnowledgeDocSchema(
        id="1",
        title="景区概况介绍",
        category="景区信息",
        content="本景区始建于明代...",
        file_path="/docs/overview.pdf",
        upload_time="2026-03-20 10:00",
        status="active",
    ),
    KnowledgeDocSchema(
        id="2",
        title="古建筑群历史",
        category="历史文化",
        content="古建筑群占地面积...",
        file_path="/docs/architecture.pdf",
        upload_time="2026-03-20 10:15",
        status="active",
    ),
    KnowledgeDocSchema(
        id="3",
        title="游览路线指南",
        category="游览信息",
        content="推荐路线一：经典路线...",
        file_path="/docs/routes.pdf",
        upload_time="2026-03-21 09:00",
        status="active",
    ),
    KnowledgeDocSchema(
        id="4",
        title="常见问题FAQ",
        category="FAQ",
        content="开放时间：8:00-18:00...",
        file_path="/docs/faq.pdf",
        upload_time="2026-03-21 09:30",
        status="active",
    ),
]


@router.get("/list", response_model=list[KnowledgeDocSchema])
async def list_docs():
    return _docs_store


@router.post("/upload", response_model=KnowledgeDocSchema)
async def upload_doc(file: UploadFile = File(...)):
    content = await file.read()
    text_content = content.decode("utf-8", errors="ignore")[:2000]

    doc = KnowledgeDocSchema(
        id=str(uuid.uuid4()),
        title=file.filename or "untitled",
        category="待分类",
        content=text_content,
        file_path=f"/uploads/{file.filename}",
        upload_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        status="active",
    )
    _docs_store.append(doc)

    rag_engine.add_document(
        title=doc.title,
        content=text_content,
        category=doc.category,
        tags=[],
    )

    return doc


@router.delete("/{doc_id}")
async def delete_doc(doc_id: str):
    global _docs_store
    _docs_store = [d for d in _docs_store if d.id != doc_id]
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
