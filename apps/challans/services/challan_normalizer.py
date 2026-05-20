from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


class ChallanNormalizer:
    """Maps ChallanPay find-challans payload into canonical records."""

    @classmethod
    def normalize_list(cls, raw: dict, vehicle_number: str) -> list[dict]:
        items = cls._extract_challan_list(raw)
        results = []
        for item in items:
            if not item:
                continue
            normalized = cls.normalize_item(item, vehicle_number)
            if normalized.get("challan_number"):
                results.append(normalized)
        return results

    @classmethod
    def normalize_item(cls, item: dict, vehicle_number: str) -> dict:
        offense_name = str(item.get("offenseName") or item.get("offenceName") or "").strip()
        offences: list = []
        if offense_name:
            offences.append(
                {
                    "name": offense_name,
                    "place": item.get("challanPlace") or "",
                    "rto": item.get("rto") or "",
                }
            )

        amount = cls._parse_amount(item.get("amount") or item.get("totalAmount") or 0)
        raw_status = str(item.get("challanStatus") or item.get("status") or "Pending")

        return {
            "challan_number": str(
                item.get("challanNo") or item.get("challanNumber") or item.get("challan_no") or ""
            ).strip(),
            "vehicle_number": str(item.get("vehicleNo") or item.get("vehicleNumber") or vehicle_number).upper(),
            "amount": str(amount),
            "status": cls._map_status(raw_status),
            "issue_date": cls._parse_date(item.get("challanDate") or item.get("issueDate")),
            "state": str(item.get("stateCode") or item.get("state") or ""),
            "city_name": str(item.get("challanPlace") or "")[:64],
            "offences": offences,
            "source": "challanpay",
            "is_court_challan": bool(item.get("courtChallan")),
            "external_challan_id": item.get("id"),
            "_raw": item,
        }

    @staticmethod
    def _map_status(raw: str) -> str:
        normalized = raw.strip().upper()
        if normalized in ("PENDING", "UNPAID", "OPEN"):
            return "PENDING"
        if normalized in ("DISPOSED", "PAID", "CLOSED", "SETTLED"):
            return "PAID"
        return normalized[:32] if normalized else "PENDING"

    @classmethod
    def _extract_challan_list(cls, raw: dict) -> list[dict]:
        if not isinstance(raw, dict):
            return raw if isinstance(raw, list) else []

        # Combined response from our client
        if "find_challans" in raw:
            return cls._extract_challan_list(raw["find_challans"])

        data = raw.get("data")
        if isinstance(data, dict):
            challans = data.get("challans")
            if isinstance(challans, list):
                return challans

        for key in ("challans", "challanList", "results"):
            val = raw.get(key)
            if isinstance(val, list):
                return val

        if isinstance(data, list):
            return data

        return []

    @staticmethod
    def _parse_amount(value: Any) -> Decimal:
        try:
            return Decimal(str(value).replace(",", "").strip() or "0")
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _parse_date(value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(value[:19], fmt).date().isoformat()
                except ValueError:
                    continue
        return str(value)
