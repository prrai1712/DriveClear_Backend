from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success_response(
    *,
    message: str = "Success",
    data: Any = None,
    meta: dict | None = None,
    status_code: int = status.HTTP_200_OK,
) -> Response:
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
            "meta": meta or {},
            "error": None,
        },
        status=status_code,
    )


def error_response(
    *,
    message: str,
    code: str,
    details: str | dict | None = None,
    meta: dict | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    return Response(
        {
            "success": False,
            "message": message,
            "data": None,
            "meta": meta or {},
            "error": {
                "code": code,
                "details": details or "",
            },
        },
        status=status_code,
    )
