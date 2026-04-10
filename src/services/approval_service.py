from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, status

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models.documents import DocumentApproval, Notification
from repositories.document_repository import DocumentRepository
from repositories.notification_repository import NotificationRepository
from repositories.route_repository import RouteRepository
from schemas.documents import DocumentSubmitDTO
from security import CurrentUser

PUBLISHED_STATUS_ID = 1
DRAFT_STATUS_ID = 2
IN_PROGRESS_STATUS_ID = 3
RETURNED_STATUS_ID = 4

def _route_start_step(route_nodes) -> int:
    if not route_nodes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval route has no nodes",
        )
    return min(node.step_index for node in route_nodes)


async def submit_document_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document_id: UUID,
    payload: DocumentSubmitDTO,
):
    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.author_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author can submit this document",
        )

    route = await RouteRepository.get_route(payload.route_id, db)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval route not found")

    if route.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Route belongs to another company",
        )

    latest_version = await DocumentRepository.get_latest_document_version(document_id, db)
    if not latest_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must have at least one version before submission",
        )

    route_nodes = sorted(route.nodes, key=lambda n: (n.step_index, n.id))
    start_step = _route_start_step(route_nodes)
    start_node = next((node for node in route_nodes if node.step_index == start_step), None)
    if not start_node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to resolve first approval node",
        )

    existing = await DocumentRepository.get_document_approval_by_step(
        document_id=cast(UUID, document.id),
        version_id=latest_version.id,
        step_index=start_node.step_index,
        db=db,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already submitted to this route",
        )

    try:
        document.route_id = route.id
        document.current_step_index = start_node.step_index
        document.status_id = IN_PROGRESS_STATUS_ID

        await DocumentRepository.create_document_approval(
            DocumentApproval(
                version_id=latest_version.id,
                document_id=document.id,
                approver_id=start_node.approver_id,
                step_index=start_node.step_index,
                is_approved=None,
                comment=None,
            ),
            db,
        )


        notification = Notification(
                user_id=start_node.approver_id,
                document_id=document.id,
                message=f"Document '{document.title}' requires your approval at step {start_node.step_index}",
            )

        await NotificationRepository.create_notification(notification, db)

        await db.commit()
        await db.refresh(document)
        return document
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while submitting document",
        ) from e


async def approve_document_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document_id: UUID,
):
    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.route_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not attached to an approval route",
        )

    latest_version = await DocumentRepository.get_latest_document_version(document_id, db)
    if not latest_version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no versions")

    current_node = await RouteRepository.get_route_node(
        document.route_id,
        document.current_step_index,
        db,
    )
    if not current_node:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current approval step cannot be resolved from the route graph",
        )

    if current_node.approver_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the current approver",
        )

    existing = await DocumentRepository.get_document_approval_by_step(
        document_id= cast(UUID, document.id),
        version_id=latest_version.id,
        step_index=current_node.step_index,
        db=db,
    )
    if existing and existing.is_approved is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This step was already processed",
        )

    next_nodes = await RouteRepository.get_next_route_nodes(document.route_id, current_node.id, db)
    if len(next_nodes) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parallel branches are not supported by the current document state model",
        )

    try:
        if existing is None:
            await DocumentRepository.create_document_approval(
                DocumentApproval(
                    version_id=latest_version.id,
                    document_id=document.id,
                    approver_id=current_user.user_id,
                    step_index=current_node.step_index,
                    is_approved=True,
                    comment=None,
                ),
                db,
            )
        else:
            existing.is_approved = True

        if next_nodes:
            next_node = next_nodes[0]
            document.current_step_index = next_node.step_index
            document.status_id = IN_PROGRESS_STATUS_ID

            await DocumentRepository.create_document_approval(
                DocumentApproval(
                    version_id=latest_version.id,
                    document_id=document.id,
                    approver_id=next_node.approver_id,
                    step_index=next_node.step_index,
                    is_approved=None,
                    comment=None,
                ),
                db,
            )

            notification = Notification(
                user_id=next_node.approver_id,
                document_id=document.id,
                message=f"Document '{document.title}' requires your approval at step {next_node.step_index}",
            )

            await NotificationRepository.create_notification(notification, db)
        else:
            document.status_id = PUBLISHED_STATUS_ID

            db.add(
                Notification(
                    user_id=document.author_id,
                    document_id=document.id,
                    message=f"Document '{document.title}' has been fully approved and published",
                )
            )

        await db.commit()
        await db.refresh(document)
        return document
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while approving document",
        ) from e


async def reject_document_service(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    document_id: UUID,
    comment: str,
):
    if not comment or not comment.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection comment is required",
        )

    document = await DocumentRepository.get_document_by_id(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.route_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not attached to an approval route",
        )

    latest_version = await DocumentRepository.get_latest_document_version(document_id, db)
    if not latest_version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no versions")

    current_node = await RouteRepository.get_route_node(
        document.route_id,
        document.current_step_index,
        db,
    )
    if not current_node:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current approval step cannot be resolved from the route graph",
        )

    if current_node.approver_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the current approver",
        )

    existing = await DocumentRepository.get_document_approval_by_step(
        document_id=cast(UUID, document.id),
        version_id=latest_version.id,
        step_index=current_node.step_index,
        db=db,
    )

    try:
        if existing is None:
            await DocumentRepository.create_document_approval(
                DocumentApproval(
                    version_id=latest_version.id,
                    document_id=document.id,
                    approver_id=current_user.user_id,
                    step_index=current_node.step_index,
                    is_approved=False,
                    comment=comment.strip(),
                ),
                db,
            )
        else:
            existing.is_approved = False
            existing.comment = comment.strip()

        document.status_id = RETURNED_STATUS_ID
        document.current_step_index = current_node.step_index

        notification = Notification(
                user_id=document.author_id,
                document_id=document.id,
                message=f"Document '{document.title}' was rejected: {comment.strip()}",
            )

        await NotificationRepository.create_notification(notification, db)

        await db.commit()
        await db.refresh(document)
        return document
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while rejecting document",
        ) from e