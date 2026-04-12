from sqlalchemy import UUID, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.approval_routes import ApprovalRoute, RouteEdge, RouteNode
from src.models.views import MVRoute

class RouteRepository:
    
    @staticmethod
    async def create_route(route: ApprovalRoute, db: AsyncSession) -> ApprovalRoute:
        db.add(route)
        await db.flush()
        return route

    @staticmethod
    async def get_route_by_id(route_id: int, db: AsyncSession) -> ApprovalRoute | None:
        result = await db.execute(
            select(ApprovalRoute)
            .where(ApprovalRoute.id == route_id)
            .options(
                selectinload(ApprovalRoute.nodes).selectinload(RouteNode.approver),
                selectinload(ApprovalRoute.edges),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_routes(company_id: UUID, db: AsyncSession):
        result = await db.execute(
            select(ApprovalRoute)
            .where(ApprovalRoute.company_id == company_id)
            .options(
                selectinload(ApprovalRoute.nodes).selectinload(RouteNode.approver),
                selectinload(ApprovalRoute.edges),
            )
            .order_by(ApprovalRoute.id.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def delete_route(route: ApprovalRoute, db: AsyncSession) -> None:
        await db.delete(route)

    @staticmethod
    async def create_node(node: RouteNode, db: AsyncSession) -> RouteNode:
        db.add(node)
        await db.flush()
        return node

    @staticmethod
    async def get_node(node_id: int, db: AsyncSession) -> RouteNode | None:
        result = await db.execute(
            select(RouteNode)
            .where(RouteNode.id == node_id)
            .options(selectinload(RouteNode.approver))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_node(node: RouteNode, db: AsyncSession) -> None:
        await db.delete(node)

    @staticmethod
    async def create_edge(edge: RouteEdge, db: AsyncSession) -> RouteEdge:
        db.add(edge)
        await db.flush()
        return edge

    @staticmethod
    async def get_edge(edge_id: int, db: AsyncSession) -> RouteEdge | None:
        result = await db.execute(select(RouteEdge).where(RouteEdge.id == edge_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_edge(edge: RouteEdge, db: AsyncSession) -> None:
        await db.delete(edge)

    @staticmethod
    async def edge_exists(route_id: int, from_node_id: int, to_node_id: int, db: AsyncSession) -> bool:
        result = await db.execute(
            select(RouteEdge.id).where(
                RouteEdge.route_id == route_id,
                RouteEdge.from_node_id == from_node_id,
                RouteEdge.to_node_id == to_node_id,
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def get_route(route_id: int, db: AsyncSession) -> ApprovalRoute | None:
        result = await db.execute(select(ApprovalRoute).where(ApprovalRoute.id == route_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_route_node(route_id: int, step_index: int, db: AsyncSession) -> RouteNode | None:
        result = await db.execute(
            select(RouteNode).where(
                and_(
                    RouteNode.route_id == route_id,
                    RouteNode.step_index == step_index,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_next_route_nodes(route_id: int, from_node_id: int, db: AsyncSession):
        result = await db.execute(
            select(RouteNode)
            .join(RouteEdge, RouteEdge.to_node_id == RouteNode.id)
            .where(
                and_(
                    RouteEdge.route_id == route_id,
                    RouteEdge.from_node_id == from_node_id,
                )
            )
            .order_by(RouteNode.step_index.asc(), RouteNode.id.asc())
        )
        return result.scalars().all()
        
    
        
        
        
        