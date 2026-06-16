import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.schemas import ChatCitation
from app.modules.documents.service import (
    create_placeholder_embedding,
    get_source_elements_for_summaries,
    search_source_element_summaries,
)


def create_placeholder_answer(question: str, evidence_texts: list[str]) -> str:
    if not evidence_texts:
        return "I could not find relevant source content for that question."

    joined_evidence = " ".join(evidence_texts)
    preview = joined_evidence[:500]

    return f"Based on the retrieved source content: {preview}"


async def answer_workspace_question(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    question: str,
    limit: int,
) -> tuple[str, list[ChatCitation]]:
    query_embedding = create_placeholder_embedding(question)
    summary_results = await search_source_element_summaries(
        db=db,
        workspace_id=workspace_id,
        owner_id=owner_id,
        query_embedding=query_embedding,
        limit=limit,
    )
    source_elements = await get_source_elements_for_summaries(
        db=db,
        workspace_id=workspace_id,
        owner_id=owner_id,
        summary_results=summary_results,
    )

    evidence_texts = [
        source_element.raw_content_text for source_element in source_elements
    ]
    answer = create_placeholder_answer(question=question, evidence_texts=evidence_texts)

    citations = [
        ChatCitation(
            source_element_id=source_element.id,
            document_id=source_element.document_id,
            workspace_id=source_element.workspace_id,
            snippet=source_element.raw_content_text[:200],
        )
        for source_element in source_elements
    ]

    return answer, citations
