"""Inventory management routes."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class ReorderRequest(BaseModel):
    """Reorder request model."""

    item_id: str = Field(..., description="Item ID to reorder")
    quantity: int = Field(..., gt=0, description="Quantity to reorder")
    priority: str = Field(default="normal", description="Order priority: low, normal, high, urgent")


class ReorderResponse(BaseModel):
    """Reorder response model."""

    order_id: str
    item_id: str
    quantity: int
    priority: str
    status: str
    estimated_delivery: str
    created_at: datetime


# Mock inventory data
MOCK_INVENTORY = {
    "ELISA_plates_96": {
        "id": "ELISA_plates_96",
        "name": "96-well ELISA Plates",
        "category": "consumables",
        "quantity": 50,
        "unit": "plates",
        "reorder_level": 20,
        "location": "Storage A1",
    },
    "pcr_tubes_200": {
        "id": "pcr_tubes_200",
        "name": "200µL PCR Tubes",
        "category": "consumables",
        "quantity": 500,
        "unit": "tubes",
        "reorder_level": 100,
        "location": "Storage A2",
    },
    "dmem_media": {
        "id": "dmem_media",
        "name": "DMEM Cell Culture Medium",
        "category": "media",
        "quantity": 10,
        "unit": "bottles",
        "reorder_level": 5,
        "location": "Cold Storage B1",
    },
    "fbs_serum": {
        "id": "fbs_serum",
        "name": "Fetal Bovine Serum",
        "category": "reagents",
        "quantity": 3,
        "unit": "bottles",
        "reorder_level": 2,
        "location": "Cold Storage B2",
    },
    "antibody_anti_il6": {
        "id": "antibody_anti_il6",
        "name": "Anti-IL-6 Capture Antibody",
        "category": "antibodies",
        "quantity": 1,
        "unit": "vials",
        "reorder_level": 1,
        "location": "Cold Storage C1",
    },
}


@router.get("/", response_model=dict[str, Any])
async def get_inventory() -> dict[str, Any]:
    """Get all inventory items.

    Returns:
        Complete inventory with all items and their stock levels.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "items": MOCK_INVENTORY,
        "total_items": len(MOCK_INVENTORY),
    }


@router.get("/{item_id}", response_model=dict[str, Any])
async def get_inventory_item(item_id: str) -> dict[str, Any]:
    """Get specific inventory item.

    Args:
        item_id: Unique item identifier.

    Returns:
        Item details and stock information.

    Raises:
        HTTPException: If item not found.
    """
    if item_id not in MOCK_INVENTORY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return MOCK_INVENTORY[item_id]


@router.post("/reorder", response_model=ReorderResponse, status_code=status.HTTP_201_CREATED)
async def reorder_item(request: ReorderRequest) -> ReorderResponse:
    """Submit a reorder request for an inventory item.

    Args:
        request: Reorder request with item ID, quantity, and priority.

    Returns:
        Created order with estimated delivery date.
    """
    if request.item_id not in MOCK_INVENTORY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{hash(request.item_id) % 10000:04d}"

    # Estimate delivery based on priority
    delivery_days = {
        "low": 14,
        "normal": 7,
        "high": 3,
        "urgent": 1,
    }
    days = delivery_days.get(request.priority, 7)

    return ReorderResponse(
        order_id=order_id,
        item_id=request.item_id,
        quantity=request.quantity,
        priority=request.priority,
        status="submitted",
        estimated_delivery=f"{days} business days",
        created_at=datetime.utcnow(),
    )
