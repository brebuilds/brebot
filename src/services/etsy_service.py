"""
Etsy Marketplace Integration Service for BreBot
Provides comprehensive e-commerce management capabilities with activity logging
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


class EtsyListing(BaseModel):
    """Etsy listing model."""
    listing_id: int
    title: str
    description: str
    state: str
    price: str
    currency_code: str
    quantity: int
    tags: List[str] = []
    materials: List[str] = []
    category_id: Optional[int] = None
    taxonomy_id: Optional[int] = None
    created_timestamp: Optional[int] = None
    updated_timestamp: Optional[int] = None
    views: Optional[int] = None
    num_favorers: Optional[int] = None


class EtsyShop(BaseModel):
    """Etsy shop model."""
    shop_id: int
    shop_name: str
    user_id: int
    creation_timestamp: int
    title: Optional[str] = None
    announcement: Optional[str] = None
    currency_code: str
    is_vacation: bool = False
    vacation_message: Optional[str] = None
    sale_message: Optional[str] = None
    digital_sale_message: Optional[str] = None
    listing_active_count: int = 0
    digital_listing_count: int = 0
    login_name: str
    accepts_custom_requests: bool = False
    policy_welcome: Optional[str] = None
    policy_payment: Optional[str] = None
    policy_shipping: Optional[str] = None
    policy_refunds: Optional[str] = None
    policy_additional: Optional[str] = None
    policy_seller_info: Optional[str] = None
    policy_updated_timestamp: Optional[int] = None
    policy_has_private_receipt_info: bool = False
    has_unstructured_policies: bool = False
    policy_privacy: Optional[str] = None
    vacation_autoreply: Optional[str] = None
    ga_code: Optional[str] = None
    structured_policies: Optional[Dict] = None
    has_onboarded_structured_policies: bool = False
    has_unstructured_policies: bool = False
    include_dispute_form_link: bool = False
    is_direct_checkout_onboarded: bool = False
    is_calculated_eligible: bool = False
    is_opted_in_to_buyer_promise: bool = False
    is_shop_us_based: bool = False
    transaction_sold_count: int = 0
    shipping_from_country_iso: Optional[str] = None
    shop_location_country_iso: Optional[str] = None


class EtsyTransaction(BaseModel):
    """Etsy transaction model."""
    transaction_id: int
    title: str
    description: str
    seller_user_id: int
    buyer_user_id: int
    creation_timestamp: int
    paid_timestamp: Optional[int] = None
    shipped_timestamp: Optional[int] = None
    price: str
    currency_code: str
    quantity: int
    tags: List[str] = []
    materials: List[str] = []
    image_listing_id: Optional[int] = None
    receipt_id: int
    shipping_cost: str
    is_digital: bool = False
    file_data: Optional[str] = None
    listing_id: int
    is_quick_sale: bool = False
    seller_feedback_id: Optional[int] = None
    buyer_feedback_id: Optional[int] = None
    transaction_type: str
    url: str
    variations: List[Dict] = []


class EtsyService:
    """Service for managing Etsy shop, listings, and orders."""
    
    def __init__(self, api_key: str, shop_id: Optional[int] = None):
        """
        Initialize Etsy service.
        
        Args:
            api_key: Etsy API key
            shop_id: Optional default shop ID
        """
        self.api_key = api_key
        self.shop_id = shop_id
        self.base_url = "https://openapi.etsy.com/v3"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        brebot_logger.log_agent_action(
            agent_name="EtsyService",
            action="initialized",
            details={"has_api_key": bool(api_key), "shop_id": shop_id}
        )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Etsy API."""
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
                    context=f"EtsyService._make_request",
                    details={"method": method, "endpoint": endpoint, "status": getattr(e.response, 'status_code', None)}
                )
                raise Exception(f"Etsy API error: {e}")
    
    async def get_shop_info(self, shop_id: Optional[int] = None, agent_name: str = "EtsyService") -> EtsyShop:
        """Get shop information."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting shop info for shop: {target_shop_id}",
                resource_id=str(target_shop_id)
            )
            
            data = await self._make_request('GET', f'/application/shops/{target_shop_id}')
            
            shop = EtsyShop(**data)
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved shop info: {shop.shop_name}",
                resource_id=str(target_shop_id),
                details={"shop_name": shop.shop_name, "listing_count": shop.listing_active_count}
            )
            
            return shop
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get shop info",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="EtsyService.get_shop_info")
            raise
    
    async def get_shop_listings(
        self, 
        shop_id: Optional[int] = None, 
        state: str = "active",
        limit: int = 25,
        offset: int = 0,
        agent_name: str = "EtsyService"
    ) -> List[EtsyListing]:
        """Get shop listings."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting listings for shop: {target_shop_id}",
                resource_id=str(target_shop_id),
                details={"state": state, "limit": limit, "offset": offset}
            )
            
            params = {"state": state, "limit": limit, "offset": offset}
            data = await self._make_request('GET', f'/application/shops/{target_shop_id}/listings', params=params)
            
            listings = []
            for listing_data in data.get('results', []):
                listing = EtsyListing(
                    listing_id=listing_data['listing_id'],
                    title=listing_data['title'],
                    description=listing_data.get('description', ''),
                    state=listing_data['state'],
                    price=listing_data['price']['amount'],
                    currency_code=listing_data['price']['currency_code'],
                    quantity=listing_data['quantity'],
                    tags=listing_data.get('tags', []),
                    materials=listing_data.get('materials', []),
                    category_id=listing_data.get('category_id'),
                    taxonomy_id=listing_data.get('taxonomy_id'),
                    created_timestamp=listing_data.get('created_timestamp'),
                    updated_timestamp=listing_data.get('updated_timestamp'),
                    views=listing_data.get('views'),
                    num_favorers=listing_data.get('num_favorers')
                )
                listings.append(listing)
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(listings)} listings",
                resource_id=str(target_shop_id),
                details={"listings_count": len(listings), "state": state}
            )
            
            return listings
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get shop listings",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="EtsyService.get_shop_listings")
            raise
    
    async def create_listing(
        self, 
        title: str,
        description: str,
        price: float,
        quantity: int,
        tags: List[str],
        materials: List[str],
        taxonomy_id: int,
        who_made: str = "i_did",
        when_made: str = "2020_2023",
        is_supply: bool = False,
        shop_id: Optional[int] = None,
        agent_name: str = "EtsyService"
    ) -> EtsyListing:
        """Create a new listing."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Creating listing: {title}",
                resource_id=str(target_shop_id),
                details={"title": title, "price": price, "quantity": quantity}
            )
            
            payload = {
                "quantity": quantity,
                "title": title,
                "description": description,
                "price": price,
                "who_made": who_made,
                "when_made": when_made,
                "taxonomy_id": taxonomy_id,
                "tags": tags[:13],  # Etsy allows max 13 tags
                "materials": materials[:13],  # Etsy allows max 13 materials
                "is_supply": is_supply,
                "state": "draft"  # Create as draft first
            }
            
            data = await self._make_request('POST', f'/application/shops/{target_shop_id}/listings', json=payload)
            
            listing = EtsyListing(
                listing_id=data['listing_id'],
                title=data['title'],
                description=data.get('description', ''),
                state=data['state'],
                price=data['price']['amount'],
                currency_code=data['price']['currency_code'],
                quantity=data['quantity'],
                tags=data.get('tags', []),
                materials=data.get('materials', []),
                taxonomy_id=data.get('taxonomy_id'),
                created_timestamp=data.get('created_timestamp'),
                updated_timestamp=data.get('updated_timestamp')
            )
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description=f"Successfully created listing: {listing.listing_id}",
                resource_id=f"{target_shop_id}/{listing.listing_id}",
                details={"listing_id": listing.listing_id, "title": title}
            )
            
            return listing
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.CREATE,
                agent_name=agent_name,
                description="Failed to create listing",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e),
                details={"title": title}
            )
            brebot_logger.log_error(e, context="EtsyService.create_listing")
            raise
    
    async def update_listing(
        self, 
        listing_id: int,
        updates: Dict[str, Any],
        shop_id: Optional[int] = None,
        agent_name: str = "EtsyService"
    ) -> EtsyListing:
        """Update an existing listing."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Updating listing: {listing_id}",
                resource_id=f"{target_shop_id}/{listing_id}",
                details={"updates": list(updates.keys())}
            )
            
            data = await self._make_request('PATCH', f'/application/shops/{target_shop_id}/listings/{listing_id}', json=updates)
            
            listing = EtsyListing(
                listing_id=data['listing_id'],
                title=data['title'],
                description=data.get('description', ''),
                state=data['state'],
                price=data['price']['amount'],
                currency_code=data['price']['currency_code'],
                quantity=data['quantity'],
                tags=data.get('tags', []),
                materials=data.get('materials', []),
                taxonomy_id=data.get('taxonomy_id'),
                created_timestamp=data.get('created_timestamp'),
                updated_timestamp=data.get('updated_timestamp'),
                views=data.get('views'),
                num_favorers=data.get('num_favorers')
            )
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description=f"Successfully updated listing",
                resource_id=f"{target_shop_id}/{listing_id}",
                details={"updates": list(updates.keys())}
            )
            
            return listing
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.UPDATE,
                agent_name=agent_name,
                description="Failed to update listing",
                resource_id=f"{target_shop_id}/{listing_id}",
                success=False,
                error_message=str(e),
                details={"attempted_updates": list(updates.keys())}
            )
            brebot_logger.log_error(e, context="EtsyService.update_listing")
            raise
    
    async def delete_listing(
        self, 
        listing_id: int,
        shop_id: Optional[int] = None,
        agent_name: str = "EtsyService"
    ) -> bool:
        """Delete a listing."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Deleting listing: {listing_id}",
                resource_id=f"{target_shop_id}/{listing_id}"
            )
            
            await self._make_request('DELETE', f'/application/shops/{target_shop_id}/listings/{listing_id}')
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description=f"Successfully deleted listing",
                resource_id=f"{target_shop_id}/{listing_id}"
            )
            
            return True
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.DELETE,
                agent_name=agent_name,
                description="Failed to delete listing",
                resource_id=f"{target_shop_id}/{listing_id}",
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="EtsyService.delete_listing")
            raise
    
    async def get_shop_receipts(
        self, 
        shop_id: Optional[int] = None,
        limit: int = 25,
        offset: int = 0,
        agent_name: str = "EtsyService"
    ) -> List[Dict[str, Any]]:
        """Get shop order receipts."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting receipts for shop: {target_shop_id}",
                resource_id=str(target_shop_id),
                details={"limit": limit, "offset": offset}
            )
            
            params = {"limit": limit, "offset": offset}
            data = await self._make_request('GET', f'/application/shops/{target_shop_id}/receipts', params=params)
            
            receipts = data.get('results', [])
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully retrieved {len(receipts)} receipts",
                resource_id=str(target_shop_id),
                details={"receipts_count": len(receipts)}
            )
            
            return receipts
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get shop receipts",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="EtsyService.get_shop_receipts")
            raise
    
    async def search_listings(
        self, 
        keywords: str,
        limit: int = 25,
        offset: int = 0,
        category: Optional[str] = None,
        agent_name: str = "EtsyService"
    ) -> List[EtsyListing]:
        """Search for listings across Etsy."""
        try:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Searching listings for: {keywords}",
                details={"keywords": keywords, "category": category, "limit": limit}
            )
            
            params = {
                "keywords": keywords,
                "limit": limit,
                "offset": offset
            }
            if category:
                params["category"] = category
            
            data = await self._make_request('GET', '/application/listings/active', params=params)
            
            listings = []
            for listing_data in data.get('results', []):
                listing = EtsyListing(
                    listing_id=listing_data['listing_id'],
                    title=listing_data['title'],
                    description=listing_data.get('description', ''),
                    state=listing_data['state'],
                    price=listing_data['price']['amount'],
                    currency_code=listing_data['price']['currency_code'],
                    quantity=listing_data['quantity'],
                    tags=listing_data.get('tags', []),
                    materials=listing_data.get('materials', []),
                    category_id=listing_data.get('category_id'),
                    taxonomy_id=listing_data.get('taxonomy_id'),
                    created_timestamp=listing_data.get('created_timestamp'),
                    updated_timestamp=listing_data.get('updated_timestamp'),
                    views=listing_data.get('views'),
                    num_favorers=listing_data.get('num_favorers')
                )
                listings.append(listing)
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Search found {len(listings)} listings",
                details={"keywords": keywords, "results_count": len(listings)}
            )
            
            return listings
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Search failed",
                success=False,
                error_message=str(e),
                details={"keywords": keywords}
            )
            brebot_logger.log_error(e, context="EtsyService.search_listings")
            raise
    
    async def get_shop_stats(
        self, 
        shop_id: Optional[int] = None,
        agent_name: str = "EtsyService"
    ) -> Dict[str, Any]:
        """Get shop statistics and metrics."""
        try:
            target_shop_id = shop_id or self.shop_id
            if not target_shop_id:
                raise ValueError("Shop ID is required")
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Getting shop statistics for: {target_shop_id}",
                resource_id=str(target_shop_id)
            )
            
            # Get shop info and listings to compile stats
            shop = await self.get_shop_info(target_shop_id, agent_name)
            listings = await self.get_shop_listings(target_shop_id, "active", limit=100, agent_name=agent_name)
            receipts = await self.get_shop_receipts(target_shop_id, limit=100, agent_name=agent_name)
            
            total_views = sum(listing.views or 0 for listing in listings)
            total_favorers = sum(listing.num_favorers or 0 for listing in listings)
            
            stats = {
                "shop_name": shop.shop_name,
                "active_listings": len(listings),
                "total_listings": shop.listing_active_count,
                "total_sales": shop.transaction_sold_count,
                "recent_orders": len(receipts),
                "total_views": total_views,
                "total_favorers": total_favorers,
                "average_price": sum(float(listing.price) for listing in listings) / len(listings) if listings else 0,
                "currency": shop.currency_code,
                "is_vacation": shop.is_vacation,
                "created_date": datetime.fromtimestamp(shop.creation_timestamp).isoformat() if shop.creation_timestamp else None
            }
            
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description=f"Successfully compiled shop statistics",
                resource_id=str(target_shop_id),
                details=stats
            )
            
            return stats
            
        except Exception as e:
            await log_platform_activity(
                platform=Platform.ETSY,
                activity_type=ActivityType.READ,
                agent_name=agent_name,
                description="Failed to get shop statistics",
                resource_id=str(target_shop_id),
                success=False,
                error_message=str(e)
            )
            brebot_logger.log_error(e, context="EtsyService.get_shop_stats")
            raise


# Global Etsy service instance
etsy_service: Optional[EtsyService] = None

def initialize_etsy_service(api_key: str, shop_id: Optional[int] = None) -> EtsyService:
    """Initialize the global Etsy service instance."""
    global etsy_service
    etsy_service = EtsyService(api_key, shop_id)
    return etsy_service

def get_etsy_service() -> Optional[EtsyService]:
    """Get the global Etsy service instance."""
    return etsy_service