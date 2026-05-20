from rest_framework.views import APIView

from apps.vehicles.repositories.vehicle_repository import VehicleRepository
from common.responses.api_response import success_response


class RecentVehiclesView(APIView):
    """Vehicles the user has searched recently (for quick re-search)."""

    def get(self, request):
        vehicles = VehicleRepository().list_recent_for_user(request.user.id, limit=8)
        data = [
            {
                "vehicle_number": v.vehicle_number,
                "vehicle_type": v.vehicle_type,
                "display_label": v.display_label or "",
                "maker_model": (v.external_metadata or {}).get("maker_model", ""),
                "last_searched_at": v.last_searched_at,
                "search_count": v.search_count,
            }
            for v in vehicles
        ]
        return success_response(message="Recent vehicles", data=data)
