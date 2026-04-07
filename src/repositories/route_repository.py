from sqlalchemy import UUID, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.approval_routes import ApprovalRoute, RouteEdge, RouteNode
from models.views import MVRoute

class RouteRepository:
    
    @staticmethod
    async def create_route(route: ApprovalRoute, db: AsyncSession):
        db.add(route)
        
        await db.flush()
        
        return route
    
    @staticmethod
    async def get_route_by_id(route_id: int, db: AsyncSession):
        result = await db.execute(select(MVRoute).where(MVRoute.route_id == route_id))
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_routes_by_company(company_id: UUID, db: AsyncSession):
        result = await db.execute(select(MVRoute).where(MVRoute.company_id == company_id))
        
        return result.all()
    
    @staticmethod 
    async def create_node(node: RouteNode, db: AsyncSession):
        db.add(node)
        
        await db.flush()
        
        return node
    
    @staticmethod
    async def get_node_by_id(node_id: int, db:AsyncSession):
        result = await db.execute(select(RouteNode).where(RouteNode.id == node_id))
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_nodes_by_route(route_id: int, db: AsyncSession):
        result = await db.execute(select(RouteNode).where(RouteNode.route_id == route_id))
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_node(node_data: dict, node: RouteNode, db: AsyncSession):
        
        for k, v in node_data.items():
            setattr(node, k, v)
        
        await db.flush()
        
        return node

    @staticmethod
    async def delete_node(node: RouteNode, db: AsyncSession):
        await db.delete(node)
        
        await db.flush()
        
    @staticmethod
    async def create_edge(edge: RouteEdge, db: AsyncSession):
        db.add(edge)
        
        await db.flush()
        
        return edge
    
    @staticmethod
    async def get_edges_by_route(route_id: int, db: AsyncSession):
        result = await db.execute(select(RouteEdge).where(RouteEdge.route_id == route_id))
        
        return result.all()
    
    @staticmethod
    async def get_edge_by_id(edge_id: int, db: AsyncSession):
        result = await db.execute(select(RouteEdge).where(RouteEdge.id == edge_id))
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_edge(edge_data: dict, edge: RouteEdge, db: AsyncSession):
        
        for k, v in edge_data.items():
            setattr(edge, k, v)
        
        await db.flush()
        
        return edge
    
    @staticmethod
    async def delete_edge(edge: RouteEdge, db: AsyncSession):
        await db.delete(edge)
        
        await db.flush()
        
    
        
        
        
        