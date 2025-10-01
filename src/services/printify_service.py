"""
Printify Print-on-Demand Integration Service for BreBot
Provides comprehensive product and order management capabilities with activity logging
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, BinaryIO
from datetime import datetime
import httpx
from pydantic import BaseModel

from utils.logger import brebot_logger
from services.activity_logger import log_platform_activity, Platform, ActivityType


class PrintifyProduct(BaseModel):
    """Printify product model."""
    id: str
    title: str
    description: str
    tags: List[str] = []
    images: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str
    visible: bool = True
    is_locked: bool = False
    blueprint_id: Optional[int] = None
    print_provider_id: Optional[int] = None
    variants: List[Dict[str, Any]] = []
    print_areas: List[Dict[str, Any]] = []
    sales_channel_properties: List[Dict[str, Any]] = []


class PrintifyOrder(BaseModel):
    """Printify order model."""
    id: str
    reference_id: Optional[str] = None
    customer: Dict[str, Any] = {}
    address_to: Dict[str, Any] = {}
    line_items: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    total_price: int = 0
    total_shipping: int = 0
    total_tax: int = 0
    status: str = "draft"
    shipping_method: int = 1
    is_printify_express: bool = False
    is_economy_shipping: bool = False
    created_at: str
    updated_at: str


class PrintifyShop(BaseModel):
    """Printify shop model."""
    id: int
    title: str
    sales_channel: str
    created_at: str


class PrintifyService:
    """Service for managing Printify products, orders, and shops."""
    
    def __init__(self, api_token: str, shop_id: Optional[int] = None):
        """
        Initialize Printify service.
        
        Args:
            api_token: Printify API token
            shop_id: Optional default shop ID
        """
        self.api_token = api_token
        self.shop_id = shop_id
        self.base_url = "https://api.printify.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        brebot_logger.log_agent_action(
            agent_name="PrintifyService",
            action="initialized",
            details={"has_token": bool(api_token), "shop_id": shop_id}
        )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Printify API."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=30.0,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                brebot_logger.log_error(
                    e, 
                    context=f"PrintifyService._make_request",
                    details={"method": method, "endpoint": endpoint, "status": getattr(e.response, 'status_code', None)}
                )
                raise Exception(f"Printify API error: {e}")
    
    async def list_shops(self, agent_name: str = "PrintifyService") -> List[PrintifyShop]:
        """List all Printify shops."""
        try:
            await log_platform_activity(
                platform=Platform.SYSTEM,  # Using SYSTEM as Printify not in enum yet
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Listing Printify shops"
            )
            
            data = await self._make_request('GET', '/shops.json')
            
            shops = []
            for shop_data in data.get('data', []):
                shop = PrintifyShop(
                    id=shop_data['id'],
                    title=shop_data['title'],
                    sales_channel=shop_data['sales_channel'],
                    created_at=shop_data['created_at']
                )
                shops.append(shop)
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully listed {len(shops)} shops",
                details={"shops_count": len(shops)}
            )
            
            return shops
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to list shops",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.list_shops")
            raise
    
    async def list_products(
        self, 
        shop_id: Optional[int] = None,
        limit: int = 10,
        page: int = 1,
        agent_name: str = "PrintifyService"
    ) -> List[PrintifyProduct]:
        """List products from a shop."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Listing products for shop: {target_shop_id}",
                resource_id=str(target_shop_id),
                details={"limit": limit, "page": page}
            )
            
            params = {"limit": limit, "page": page}
            data = await self._make_request('GET', f'/shops/{target_shop_id}/products.json', params=params)
            
            products = []
            for product_data in data.get('data', []):
                product = PrintifyProduct(
                    id=product_data['id'],
                    title=product_data['title'],
                    description=product_data['description'],
                    tags=product_data.get('tags', []),
                    images=product_data.get('images', []),
                    created_at=product_data['created_at'],
                    updated_at=product_data['updated_at'],
                    visible=product_data.get('visible', True),
                    is_locked=product_data.get('is_locked', False),
                    blueprint_id=product_data.get('blueprint_id'),
                    print_provider_id=product_data.get('print_provider_id'),
                    variants=product_data.get('variants', []),
                    print_areas=product_data.get('print_areas', [])
                )
                products.append(product)
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(products)} products",
                resource_id=str(target_shop_id),
                details={"products_count": len(products)}
            )
            
            return products
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to list products",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.list_products")
            raise
    
    async def get_product(
        self, 
        product_id: str,
        shop_id: Optional[int] = None,
        agent_name: str = "PrintifyService"
    ) -> PrintifyProduct:
        """Get a specific product."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting product: {product_id}",
                resource_id=f"{target_shop_id}/{product_id}"
            )
            
            data = await self._make_request('GET', f'/shops/{target_shop_id}/products/{product_id}.json')
            
            product = PrintifyProduct(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                tags=data.get('tags', []),
                images=data.get('images', []),
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                visible=data.get('visible', True),
                is_locked=data.get('is_locked', False),
                blueprint_id=data.get('blueprint_id'),
                print_provider_id=data.get('print_provider_id'),
                variants=data.get('variants', []),
                print_areas=data.get('print_areas', [])
            )
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved product: {product.title}",
                resource_id=f"{target_shop_id}/{product_id}",
                details={"title": product.title}
            )
            
            return product
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get product",
                resource_id=f"{target_shop_id}/{product_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.get_product")
            raise
    
    async def create_product(
        self,
        title: str,
        description: str,
        blueprint_id: int,
        print_provider_id: int,
        variants: List[Dict[str, Any]],
        print_areas: List[Dict[str, Any]],
        shop_id: Optional[int] = None,
        tags: List[str] = None,
        agent_name: str = "PrintifyService"
    ) -> PrintifyProduct:
        """Create a new product."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Creating product: {title}",
                resource_id=str(target_shop_id),
                details={"title": title, "blueprint_id": blueprint_id, "print_provider_id": print_provider_id}
            )
            
            payload = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variants,
                "print_areas": print_areas
            }
            
            if tags:
                payload["tags"] = tags
            
            data = await self._make_request('POST', f'/shops/{target_shop_id}/products.json', json=payload)
            
            product = PrintifyProduct(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                tags=data.get('tags', []),
                images=data.get('images', []),
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                visible=data.get('visible', True),
                is_locked=data.get('is_locked', False),
                blueprint_id=data.get('blueprint_id'),
                print_provider_id=data.get('print_provider_id'),
                variants=data.get('variants', []),
                print_areas=data.get('print_areas', [])
            )
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully created product: {product.id}",
                resource_id=f"{target_shop_id}/{product.id}",
                details={"product_id": product.id, "title": title}
            )
            
            return product
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to create product",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e),
                details={"title": title}
            )
            brebot_logger.log_error(e, context="PrintifyService.create_product")
            raise
    
    async def update_product(
        self,
        product_id: str,
        updates: Dict[str, Any],
        shop_id: Optional[int] = None,
        agent_name: str = "PrintifyService"
    ) -> PrintifyProduct:
        """Update an existing product."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Updating product: {product_id}",
                resource_id=f"{target_shop_id}/{product_id}",
                details={"updates": list(updates.keys())}
            )
            
            data = await self._make_request('PUT', f'/shops/{target_shop_id}/products/{product_id}.json', json=updates)
            
            product = PrintifyProduct(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                tags=data.get('tags', []),
                images=data.get('images', []),
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                visible=data.get('visible', True),
                is_locked=data.get('is_locked', False),
                blueprint_id=data.get('blueprint_id'),
                print_provider_id=data.get('print_provider_id'),
                variants=data.get('variants', []),
                print_areas=data.get('print_areas', [])
            )
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Successfully updated product",
                resource_id=f"{target_shop_id}/{product_id}",
                details={"updates": list(updates.keys())}
            )
            
            return product
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description="Failed to update product",
                resource_id=f"{target_shop_id}/{product_id}",
                success=False,
                error_message=str(e),
                details={"attempted_updates": list(updates.keys())}
            )
            brebot_logger.log_error(e, context="PrintifyService.update_product")
            raise
    
    async def delete_product(
        self,
        product_id: str,
        shop_id: Optional[int] = None,
        agent_name: str = "PrintifyService"
    ) -> bool:
        """Delete a product."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Deleting product: {product_id}",
                resource_id=f"{target_shop_id}/{product_id}"
            )
            
            await self._make_request('DELETE', f'/shops/{target_shop_id}/products/{product_id}.json')
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Successfully deleted product",
                resource_id=f"{target_shop_id}/{product_id}"
            )
            
            return True
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description="Failed to delete product",
                resource_id=f"{target_shop_id}/{product_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.delete_product")
            raise
    
    async def publish_product(
        self,
        product_id: str,
        shop_id: Optional[int] = None,
        agent_name: str = "PrintifyService"
    ) -> Dict[str, Any]:
        """Publish a product to connected sales channels."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Publishing product: {product_id}",
                resource_id=f"{target_shop_id}/{product_id}"
            )
            
            payload = {"title": True, "description": True, "images": True, "variants": True, "tags": True}
            data = await self._make_request('POST', f'/shops/{target_shop_id}/products/{product_id}/publish.json', json=payload)
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Successfully published product",
                resource_id=f"{target_shop_id}/{product_id}",
                details={"publish_result": data}
            )
            
            return data
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description="Failed to publish product",
                resource_id=f"{target_shop_id}/{product_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.publish_product")
            raise
    
    async def list_orders(
        self,
        shop_id: Optional[int] = None,
        limit: int = 10,
        page: int = 1,
        agent_name: str = "PrintifyService"
    ) -> List[PrintifyOrder]:
        """List orders from a shop."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Listing orders for shop: {target_shop_id}",
                resource_id=str(target_shop_id),
                details={"limit": limit, "page": page}
            )
            
            params = {"limit": limit, "page": page}
            data = await self._make_request('GET', f'/shops/{target_shop_id}/orders.json', params=params)
            
            orders = []
            for order_data in data.get('data', []):
                order = PrintifyOrder(
                    id=order_data['id'],
                    reference_id=order_data.get('reference_id'),
                    customer=order_data.get('customer', {}),
                    address_to=order_data.get('address_to', {}),
                    line_items=order_data.get('line_items', []),
                    metadata=order_data.get('metadata', {}),
                    total_price=order_data.get('total_price', 0),
                    total_shipping=order_data.get('total_shipping', 0),
                    total_tax=order_data.get('total_tax', 0),
                    status=order_data.get('status', 'draft'),
                    created_at=order_data['created_at'],
                    updated_at=order_data['updated_at']
                )
                orders.append(order)
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(orders)} orders",
                resource_id=str(target_shop_id),
                details={"orders_count": len(orders)}
            )
            
            return orders
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to list orders",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.list_orders")
            raise
    
    async def create_order(
        self,
        line_items: List[Dict[str, Any]],
        address_to: Dict[str, Any],
        shop_id: Optional[int] = None,
        reference_id: Optional[str] = None,
        agent_name: str = "PrintifyService"
    ) -> PrintifyOrder:
        """Create a new order."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Creating order with {len(line_items)} items",
                resource_id=str(target_shop_id),
                details={"line_items_count": len(line_items), "reference_id": reference_id}
            )
            
            payload = {
                "line_items": line_items,
                "address_to": address_to
            }
            
            if reference_id:
                payload["reference_id"] = reference_id
            
            data = await self._make_request('POST', f'/shops/{target_shop_id}/orders.json', json=payload)
            
            order = PrintifyOrder(
                id=data['id'],
                reference_id=data.get('reference_id'),
                customer=data.get('customer', {}),
                address_to=data.get('address_to', {}),
                line_items=data.get('line_items', []),
                metadata=data.get('metadata', {}),
                total_price=data.get('total_price', 0),
                total_shipping=data.get('total_shipping', 0),
                total_tax=data.get('total_tax', 0),
                status=data.get('status', 'draft'),
                created_at=data['created_at'],
                updated_at=data['updated_at']
            )
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully created order: {order.id}",
                resource_id=f"{target_shop_id}/{order.id}",
                details={"order_id": order.id, "total_price": order.total_price}
            )
            
            return order
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to create order",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e),
                details={"line_items_count": len(line_items)}
            )
            brebot_logger.log_error(e, context="PrintifyService.create_order")
            raise
    
    async def get_blueprints(self, agent_name: str = "PrintifyService") -> List[Dict[str, Any]]:
        """Get available product blueprints."""
        try:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Getting available blueprints"
            )
            
            data = await self._make_request('GET', '/catalog/blueprints.json')
            blueprints = data.get('data', [])
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(blueprints)} blueprints",
                details={"blueprints_count": len(blueprints)}
            )
            
            return blueprints
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get blueprints",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="PrintifyService.get_blueprints")
            raise
    
    async def get_print_providers(self, blueprint_id: int, agent_name: str = "PrintifyService") -> List[Dict[str, Any]]:
        """Get print providers for a specific blueprint."""
        try:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting print providers for blueprint: {blueprint_id}",
                details={"blueprint_id": blueprint_id}
            )
            
            data = await self._make_request('GET', f'/catalog/blueprints/{blueprint_id}/print_providers.json')
            providers = data.get('data', [])
            
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(providers)} print providers",
                details={"blueprint_id": blueprint_id, "providers_count": len(providers)}
            )
            
            return providers
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.SYSTEM,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get print providers",
                success=False,
                error_message=str(e),
                details={"blueprint_id": blueprint_id}
            )
            brebot_logger.log_error(e, context="PrintifyService.get_print_providers")
            raise


# Global Printify service instance
printify_service: Optional[PrintifyService] = None

def initialize_printify_service(api_token: str, shop_id: Optional[int] = None) -> PrintifyService:
    """Initialize the global Printify service instance."""
    global printify_service
    printify_service = PrintifyService(api_token, shop_id)
    return printify_service

def get_printify_service() -> Optional[PrintifyService]:
    """Get the global Printify service instance."""
    return printify_service