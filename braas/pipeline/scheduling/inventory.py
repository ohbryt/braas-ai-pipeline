"""
BRaaS Inventory Manager - Track reagents, consumables, and tips.

Provides demand prediction using exponential smoothing, auto-reorder
capabilities, vendor selection optimization, and expiration tracking.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from braas.core.enums import (
    OrderStatus,
    ReagentCategory,
    StorageCondition,
)
from braas.core.models import Reagent

logger = logging.getLogger(__name__)


@dataclass
class ReagentStock:
    """Tracks current stock level and usage history for a reagent."""
    reagent: Reagent
    current_quantity: float = 0.0
    reserved_quantity: float = 0.0
    reorder_point: float = 0.0
    reorder_quantity: float = 0.0
    lead_time_days: int = 7
    usage_history: List[Tuple[datetime, float]] = field(default_factory=list)
    last_restocked: Optional[datetime] = None

    @property
    def available_quantity(self) -> float:
        """Quantity available after reservations."""
        return max(0.0, self.current_quantity - self.reserved_quantity)

    @property
    def needs_reorder(self) -> bool:
        """Check if stock has fallen below reorder point."""
        return self.available_quantity <= self.reorder_point

    def record_usage(self, quantity: float, timestamp: Optional[datetime] = None) -> None:
        """Record reagent usage."""
        ts = timestamp or datetime.utcnow()
        self.current_quantity = max(0.0, self.current_quantity - quantity)
        self.usage_history.append((ts, quantity))

    def restock(self, quantity: float, timestamp: Optional[datetime] = None) -> None:
        """Add stock from a delivery."""
        self.current_quantity += quantity
        self.last_restocked = timestamp or datetime.utcnow()


@dataclass
class VendorInfo:
    """Vendor information for procurement optimization."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    catalog_number: str = ""
    unit_price: float = 0.0
    bulk_discount_threshold: int = 10
    bulk_discount_pct: float = 0.0
    lead_time_days: int = 7
    reliability_score: float = 0.9  # 0-1, historical on-time delivery rate
    minimum_order: int = 1


@dataclass
class PurchaseOrder:
    """A purchase order for reagents/consumables."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vendor_name: str = ""
    status: OrderStatus = OrderStatus.DRAFT
    items: List[PurchaseOrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    total_cost: float = 0.0
    notes: str = ""

    def calculate_total(self) -> float:
        """Calculate total order cost."""
        self.total_cost = sum(item.total_price for item in self.items)
        return self.total_cost


@dataclass
class PurchaseOrderItem:
    """A line item in a purchase order."""
    reagent_id: str = ""
    reagent_name: str = ""
    quantity: float = 0.0
    unit: str = "mL"
    unit_price: float = 0.0
    vendor_catalog_number: str = ""

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


class InventoryManager:
    """
    Manages laboratory inventory including reagents, consumables, and tips.

    Provides real-time stock tracking, demand forecasting via exponential
    smoothing, automated reordering, and vendor selection optimization.
    """

    def __init__(self, smoothing_alpha: float = 0.3) -> None:
        """
        Initialize the inventory manager.

        Args:
            smoothing_alpha: Smoothing factor for exponential smoothing (0-1).
                Higher values give more weight to recent observations.
        """
        self._stock: Dict[str, ReagentStock] = {}
        self._vendors: Dict[str, List[VendorInfo]] = {}  # reagent_id -> vendors
        self._orders: List[PurchaseOrder] = []
        self._smoothing_alpha = smoothing_alpha
        logger.info("InventoryManager initialized")

    def add_reagent(self, stock: ReagentStock) -> None:
        """Add a reagent to inventory tracking."""
        self._stock[stock.reagent.id] = stock
        logger.info(
            f"Added reagent: {stock.reagent.name} "
            f"(qty={stock.current_quantity} {stock.reagent.unit})"
        )

    def add_vendor(self, reagent_id: str, vendor: VendorInfo) -> None:
        """Register a vendor for a reagent."""
        self._vendors.setdefault(reagent_id, []).append(vendor)

    async def check_availability(
        self,
        reagent_id: str,
        required_quantity: float,
    ) -> Dict[str, Any]:
        """
        Check if a reagent is available in sufficient quantity.

        Args:
            reagent_id: ID of the reagent to check.
            required_quantity: Amount needed.

        Returns:
            Dict with availability status, current stock, and recommendations.
        """
        stock = self._stock.get(reagent_id)
        if stock is None:
            return {
                "available": False,
                "reason": "Reagent not found in inventory",
                "reagent_id": reagent_id,
                "current_quantity": 0.0,
                "required_quantity": required_quantity,
            }

        available = stock.available_quantity >= required_quantity
        days_until_expiry = None
        if stock.reagent.expiration_date:
            days_until_expiry = (
                stock.reagent.expiration_date - datetime.utcnow()
            ).days

        result: Dict[str, Any] = {
            "available": available,
            "reagent_id": reagent_id,
            "reagent_name": stock.reagent.name,
            "current_quantity": stock.current_quantity,
            "reserved_quantity": stock.reserved_quantity,
            "available_quantity": stock.available_quantity,
            "required_quantity": required_quantity,
            "unit": stock.reagent.unit,
            "days_until_expiry": days_until_expiry,
            "needs_reorder": stock.needs_reorder,
        }

        if not available:
            shortfall = required_quantity - stock.available_quantity
            result["shortfall"] = shortfall
            result["reason"] = (
                f"Insufficient stock: need {required_quantity} {stock.reagent.unit}, "
                f"only {stock.available_quantity} {stock.reagent.unit} available"
            )
            result["recommendation"] = (
                f"Order at least {shortfall} {stock.reagent.unit} "
                f"(lead time: {stock.lead_time_days} days)"
            )

        if days_until_expiry is not None and days_until_expiry < 30:
            result["expiry_warning"] = (
                f"Reagent expires in {days_until_expiry} days"
            )

        return result

    async def reserve_materials(
        self,
        experiment_id: str,
        requirements: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Reserve materials for an experiment.

        Args:
            experiment_id: The experiment requesting materials.
            requirements: Dict mapping reagent_id to required quantity.

        Returns:
            Dict with reservation status for each reagent.
        """
        reservations: Dict[str, Any] = {}
        all_available = True

        for reagent_id, quantity in requirements.items():
            availability = await self.check_availability(reagent_id, quantity)

            if availability["available"]:
                stock = self._stock[reagent_id]
                stock.reserved_quantity += quantity
                reservations[reagent_id] = {
                    "status": "reserved",
                    "quantity": quantity,
                    "experiment_id": experiment_id,
                    "remaining_available": stock.available_quantity,
                }
                logger.info(
                    f"Reserved {quantity} {stock.reagent.unit} of "
                    f"{stock.reagent.name} for experiment {experiment_id}"
                )
            else:
                all_available = False
                reservations[reagent_id] = {
                    "status": "insufficient",
                    "quantity_requested": quantity,
                    "available": availability["available_quantity"],
                    "shortfall": availability.get("shortfall", 0),
                }

        return {
            "experiment_id": experiment_id,
            "all_reserved": all_available,
            "reservations": reservations,
        }

    async def predict_demand(
        self,
        reagent_id: str,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Predict future demand using exponential smoothing.

        Uses simple exponential smoothing on usage history to forecast
        daily demand, then projects over the given horizon.

        Args:
            reagent_id: Reagent to forecast demand for.
            horizon_days: Number of days to forecast.

        Returns:
            Dict with forecast details including predicted demand,
            confidence intervals, and reorder recommendations.
        """
        stock = self._stock.get(reagent_id)
        if stock is None:
            return {"error": f"Reagent {reagent_id} not found"}

        if len(stock.usage_history) < 2:
            return {
                "reagent_id": reagent_id,
                "forecast": "insufficient_data",
                "message": "Need at least 2 usage records for forecasting",
                "usage_records": len(stock.usage_history),
            }

        # Aggregate daily usage
        daily_usage = self._aggregate_daily_usage(stock.usage_history)

        if not daily_usage:
            return {
                "reagent_id": reagent_id,
                "forecast": "no_usage",
                "predicted_daily_demand": 0.0,
            }

        # Apply exponential smoothing
        smoothed = self._exponential_smoothing(daily_usage)

        # Forecast = last smoothed value (simple ES is flat forecast)
        predicted_daily = smoothed[-1] if smoothed else 0.0
        predicted_total = predicted_daily * horizon_days

        # Calculate variance for confidence intervals
        residuals = [
            abs(actual - pred)
            for actual, pred in zip(daily_usage[1:], smoothed[:-1])
        ]
        avg_error = sum(residuals) / len(residuals) if residuals else 0.0

        # Days until stockout
        if predicted_daily > 0:
            days_until_stockout = stock.available_quantity / predicted_daily
        else:
            days_until_stockout = float("inf")

        # Determine if reorder is needed within horizon
        reorder_needed = days_until_stockout < (
            horizon_days + stock.lead_time_days
        )

        result: Dict[str, Any] = {
            "reagent_id": reagent_id,
            "reagent_name": stock.reagent.name,
            "horizon_days": horizon_days,
            "predicted_daily_demand": round(predicted_daily, 4),
            "predicted_total_demand": round(predicted_total, 4),
            "confidence_interval_95": round(avg_error * 1.96, 4),
            "current_stock": stock.available_quantity,
            "days_until_stockout": round(days_until_stockout, 1),
            "reorder_needed": reorder_needed,
            "smoothing_alpha": self._smoothing_alpha,
            "data_points": len(daily_usage),
        }

        if reorder_needed:
            # Recommend order quantity to cover horizon + safety stock
            safety_stock = predicted_daily * stock.lead_time_days * 1.5
            order_qty = max(
                stock.reorder_quantity,
                predicted_total + safety_stock - stock.available_quantity,
            )
            result["recommended_order_quantity"] = round(order_qty, 2)
            result["recommended_order_date"] = (
                datetime.utcnow()
                + timedelta(days=max(0, days_until_stockout - stock.lead_time_days - 3))
            ).isoformat()

        return result

    async def auto_reorder(self) -> List[PurchaseOrder]:
        """
        Automatically generate purchase orders for reagents below reorder point.

        Groups items by best vendor to minimize number of orders.

        Returns:
            List of generated PurchaseOrder objects.
        """
        orders_created: List[PurchaseOrder] = []
        items_by_vendor: Dict[str, List[Tuple[ReagentStock, VendorInfo]]] = {}

        for reagent_id, stock in self._stock.items():
            if not stock.needs_reorder:
                continue

            # Find best vendor
            best_vendor = await self._select_best_vendor(reagent_id, stock.reorder_quantity)
            if best_vendor is None:
                logger.warning(
                    f"No vendor found for {stock.reagent.name}, cannot auto-reorder"
                )
                continue

            items_by_vendor.setdefault(best_vendor.name, []).append(
                (stock, best_vendor)
            )

        # Create one order per vendor
        for vendor_name, items in items_by_vendor.items():
            order = PurchaseOrder(
                vendor_name=vendor_name,
                status=OrderStatus.DRAFT,
            )

            for stock, vendor in items:
                order_item = PurchaseOrderItem(
                    reagent_id=stock.reagent.id,
                    reagent_name=stock.reagent.name,
                    quantity=stock.reorder_quantity,
                    unit=stock.reagent.unit,
                    unit_price=vendor.unit_price,
                    vendor_catalog_number=vendor.catalog_number,
                )
                order.items.append(order_item)

            order.calculate_total()
            order.expected_delivery = (
                datetime.utcnow()
                + timedelta(days=max(v.lead_time_days for _, v in items))
            )

            self._orders.append(order)
            orders_created.append(order)

            logger.info(
                f"Auto-reorder: Created PO {order.id} for vendor "
                f"{vendor_name} ({len(order.items)} items, ${order.total_cost:.2f})"
            )

        return orders_created

    async def get_expiring_items(
        self,
        days_threshold: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get list of items expiring within the threshold period.

        Args:
            days_threshold: Number of days to look ahead for expiration.

        Returns:
            List of dicts with reagent info and expiration details.
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(days=days_threshold)
        expiring: List[Dict[str, Any]] = []

        for stock in self._stock.values():
            exp_date = stock.reagent.expiration_date
            if exp_date is None:
                continue

            if exp_date <= cutoff:
                days_remaining = (exp_date - now).days
                expiring.append({
                    "reagent_id": stock.reagent.id,
                    "reagent_name": stock.reagent.name,
                    "expiration_date": exp_date.isoformat(),
                    "days_remaining": days_remaining,
                    "current_quantity": stock.current_quantity,
                    "unit": stock.reagent.unit,
                    "storage": stock.reagent.storage_condition.value,
                    "expired": days_remaining < 0,
                    "urgency": (
                        "expired" if days_remaining < 0
                        else "critical" if days_remaining < 7
                        else "warning" if days_remaining < 14
                        else "notice"
                    ),
                })

        # Sort by days remaining (most urgent first)
        expiring.sort(key=lambda x: x["days_remaining"])
        return expiring

    async def optimize_vendor_selection(
        self,
        reagent_id: str,
        quantity: float,
    ) -> List[Dict[str, Any]]:
        """
        Rank vendors for a reagent purchase based on multi-criteria scoring.

        Criteria:
        - Cost (40% weight): Unit price including bulk discounts
        - Reliability (30% weight): On-time delivery history
        - Lead time (20% weight): Faster is better
        - Minimum order (10% weight): Lower minimum is better

        Args:
            reagent_id: Reagent to purchase.
            quantity: Amount to order.

        Returns:
            Ranked list of vendor options with scores.
        """
        vendors = self._vendors.get(reagent_id, [])
        if not vendors:
            return []

        scored: List[Dict[str, Any]] = []

        # Calculate raw metrics
        prices = []
        lead_times = []
        for vendor in vendors:
            effective_price = vendor.unit_price
            if quantity >= vendor.bulk_discount_threshold:
                effective_price *= (1 - vendor.bulk_discount_pct / 100)
            prices.append(effective_price)
            lead_times.append(vendor.lead_time_days)

        max_price = max(prices) if prices else 1
        max_lead = max(lead_times) if lead_times else 1

        for i, vendor in enumerate(vendors):
            effective_price = prices[i]
            total_cost = effective_price * quantity

            # Normalize scores (0-1, higher is better)
            cost_score = 1.0 - (effective_price / max_price) if max_price > 0 else 0.5
            reliability_score = vendor.reliability_score
            lead_score = 1.0 - (vendor.lead_time_days / max_lead) if max_lead > 0 else 0.5
            min_order_score = 1.0 if quantity >= vendor.minimum_order else 0.0

            # Weighted total
            total_score = (
                0.4 * cost_score
                + 0.3 * reliability_score
                + 0.2 * lead_score
                + 0.1 * min_order_score
            )

            scored.append({
                "vendor_name": vendor.name,
                "catalog_number": vendor.catalog_number,
                "unit_price": round(effective_price, 2),
                "total_cost": round(total_cost, 2),
                "bulk_discount_applied": quantity >= vendor.bulk_discount_threshold,
                "lead_time_days": vendor.lead_time_days,
                "reliability_score": vendor.reliability_score,
                "meets_minimum_order": quantity >= vendor.minimum_order,
                "overall_score": round(total_score, 4),
                "score_breakdown": {
                    "cost": round(cost_score, 3),
                    "reliability": round(reliability_score, 3),
                    "lead_time": round(lead_score, 3),
                    "minimum_order": round(min_order_score, 3),
                },
            })

        scored.sort(key=lambda x: x["overall_score"], reverse=True)
        return scored

    # ── Private helpers ─────────────────────────────────────────────────

    def _aggregate_daily_usage(
        self,
        history: List[Tuple[datetime, float]],
    ) -> List[float]:
        """Aggregate usage history into daily totals."""
        if not history:
            return []

        daily: Dict[str, float] = {}
        for ts, qty in history:
            day_key = ts.strftime("%Y-%m-%d")
            daily[day_key] = daily.get(day_key, 0) + qty

        # Fill in gaps with zeros
        sorted_days = sorted(daily.keys())
        if len(sorted_days) < 2:
            return list(daily.values())

        start = datetime.strptime(sorted_days[0], "%Y-%m-%d")
        end = datetime.strptime(sorted_days[-1], "%Y-%m-%d")

        result: List[float] = []
        current = start
        while current <= end:
            key = current.strftime("%Y-%m-%d")
            result.append(daily.get(key, 0.0))
            current += timedelta(days=1)

        return result

    def _exponential_smoothing(self, data: List[float]) -> List[float]:
        """
        Apply simple exponential smoothing.

        S_t = alpha * X_t + (1 - alpha) * S_{t-1}

        Args:
            data: Time series data points.

        Returns:
            Smoothed values.
        """
        if not data:
            return []

        alpha = self._smoothing_alpha
        smoothed = [data[0]]  # Initialize with first observation

        for i in range(1, len(data)):
            s = alpha * data[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(s)

        return smoothed

    async def _select_best_vendor(
        self,
        reagent_id: str,
        quantity: float,
    ) -> Optional[VendorInfo]:
        """Select the best vendor based on optimization scoring."""
        ranked = await self.optimize_vendor_selection(reagent_id, quantity)
        if not ranked:
            return None

        best_name = ranked[0]["vendor_name"]
        for vendor in self._vendors.get(reagent_id, []):
            if vendor.name == best_name:
                return vendor
        return None
