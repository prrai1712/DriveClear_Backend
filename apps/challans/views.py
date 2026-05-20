from rest_framework.views import APIView

from apps.challans.serializers import FetchChallanSerializer
from apps.challans.services.challan_fetch_service import ChallanFetchService
from apps.challans.services.challan_serializer import ChallanResponseSerializer
from apps.challans.repositories.challan_repository import ChallanRepository
from common.responses.api_response import success_response


class FetchChallansView(APIView):
    def post(self, request):
        serializer = FetchChallanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = ChallanFetchService().fetch_for_vehicle(
            user=request.user,
            vehicle_number=serializer.validated_data["vehicle_number"],
            vehicle_type=serializer.validated_data["vehicle_type"],
        )
        if data.get("no_challans_found"):
            message = "No pending challans found for this vehicle"
        elif data.get("from_cache"):
            message = "Showing saved challan data"
        else:
            message = "Challans fetched successfully"
        return success_response(message=message, data=data)


class ListChallansView(APIView):
    def get(self, request):
        vehicle_number = request.query_params.get("vehicle_number")
        if not vehicle_number:
            return success_response(
                message="vehicle_number is required",
                data=[],
                meta={"count": 0},
            )
        challans = ChallanRepository().list_for_vehicle(
            vehicle_number.upper().strip(),
            source_name="challanpay",
        )
        data = [ChallanResponseSerializer.serialize(c) for c in challans]
        return success_response(message="Challans listed", data=data, meta={"count": len(data)})
