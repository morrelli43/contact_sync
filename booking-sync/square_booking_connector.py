"""
Square Bookings API connector.
"""
from typing import List, Optional
import os
from datetime import datetime, timezone

try:
    from square.client import Client
    SQUARE_AVAILABLE = True
except ImportError:
    SQUARE_AVAILABLE = False

from booking_model import Booking


class SquareBookingConnector:
    """Connector for Square Bookings API."""
    
    def __init__(self, access_token: str = None):
        if not SQUARE_AVAILABLE:
            raise ImportError("Square API library not installed. Run: pip install squareup")
        
        self.access_token = access_token or os.getenv('SQUARE_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("Square access token not provided. Set SQUARE_ACCESS_TOKEN environment variable.")
        
        self.client = Client(
            access_token=self.access_token,
            environment='production'
        )
        
    def fetch_upcoming_bookings(self, limit: int = 100) -> List[Booking]:
        """Fetch upcoming bookings from Square."""
        bookings = []
        
        try:
            # We want bookings that are upcoming
            # API: SearchBookings
            body = {
                "query": {
                    "filter": {
                        "start_at": {
                            "start_at": datetime.now(timezone.utc).isoformat()
                        },
                        "status": "ACCEPTED" # Or filter multiple
                    }
                },
                "limit": limit
            }
            
            result = self.client.bookings.search_bookings(body=body)
            
            if result.is_success():
                square_bookings = result.body.get('bookings', [])
                print(f"Found {len(square_bookings)} upcoming Square bookings.")
                
                for sb in square_bookings:
                    booking = self._convert_to_booking(sb)
                    if booking:
                        bookings.append(booking)
            else:
                print(f"Error searching Square bookings: {result.errors}")
                
        except Exception as e:
            print(f"Error connecting to Square API (Bookings): {e}")
            
        return bookings
    
    def _convert_to_booking(self, sb: dict) -> Optional[Booking]:
        """Convert Square booking object to Booking model."""
        booking = Booking(sb.get('id'))
        
        # Timing
        start_at = sb.get('start_at')
        if start_at:
            booking.start_at = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
            
        # Duration / End Time (Square might not provide end_at explicitly in all cases, but usually does)
        # It has appointment_segments
        segments = sb.get('appointment_segments', [])
        if segments:
            # Sum up durations or find the latest end_at?
            # Usually the booking itself has an end_at? No, let's check segments.
            # Actually, the base booking object doesn't always have end_at.
            # But it has it in recent versions or we can calculate.
            # Square docs: start_at is the start time.
            # Many segments have duration_minutes.
            total_duration = sum(s.get('duration_minutes', 0) for s in segments)
            if booking.start_at:
                from datetime import timedelta
                booking.end_at = booking.start_at + timedelta(minutes=total_duration)
            
            # Get Service Name from first segment's service_variation_id?
            # Need to fetch service catalog if we want names...
            # For now, let's just use segment metadata if present.
            booking.service_id = segments[0].get('service_variation_id')
            # service_name will need to be enriched later or fetched if possible.
        
        # Customer
        booking.customer_id = sb.get('customer_id')
        # We need to fetch the customer name for the summary.
        # Enrichment will happen in a separate step or here via cache.
        
        booking.status = sb.get('status')
        booking.notes = sb.get('customer_note', '')
        
        # Location
        location_id = sb.get('location_id')
        # Could enrich location name too.
            
        return booking

    def get_customer_details(self, customer_id: str) -> dict:
        """Fetch customer details from Square."""
        try:
            result = self.client.customers.retrieve_customer(customer_id=customer_id)
            if result.is_success():
                return result.body.get('customer', {})
        except Exception as e:
            print(f"Error fetching customer {customer_id}: {e}")
        return {}
        
    def get_service_details(self, service_variation_id: str) -> dict:
        """Fetch service details from Catalog."""
        try:
            result = self.client.catalog.retrieve_catalog_object(object_id=service_variation_id)
            if result.is_success():
                obj = result.body.get('object', {})
                # It's a item_variation, we want the item name probably.
                return obj
        except Exception as e:
            print(f"Error fetching service {service_variation_id}: {e}")
        return {}
