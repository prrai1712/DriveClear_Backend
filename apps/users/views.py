from rest_framework.views import APIView

from apps.users.serializers import UserProfileSerializer
from common.responses.api_response import success_response


class MeView(APIView):
    def get(self, request):
        return success_response(
            message="Profile fetched",
            data=UserProfileSerializer(request.user).data,
        )
