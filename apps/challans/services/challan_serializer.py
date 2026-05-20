"""Shared API shape for challan list/fetch responses."""


class ChallanResponseSerializer:
    @staticmethod
    def serialize(challan) -> dict:
        n = challan.normalized_response or {}
        raw = challan.source_response or {}
        offences = challan.offence_details or []
        offense_name = offences[0].get("name") if offences else raw.get("offenseName", "")

        amount = challan.total_amount
        status_upper = (challan.challan_status or "").upper()
        is_payable = status_upper == "PENDING" and amount > 0
        return {
            "uuid": str(challan.uuid),
            "challan_number": challan.challan_number,
            "vehicle_number": challan.vehicle_number,
            "chassis_number": challan.chassis_number or "",
            "engine_number": challan.engine_number or "",
            "amount": str(challan.total_amount),
            "total_amount": str(challan.total_amount),
            "status": challan.challan_status,
            "challan_status": challan.challan_status,
            "issue_date": str(challan.issue_date) if challan.issue_date else n.get("issue_date", ""),
            "state": challan.state_name,
            "place": challan.city_name or raw.get("challanPlace", ""),
            "offense_name": offense_name,
            "offences": offences,
            "rto": raw.get("rto", ""),
            "source": challan.source_name,
            "is_court_challan": challan.is_court_challan,
            "payment_status": challan.payment_status,
            "external_id": raw.get("id"),
            "fetched_at": challan.fetched_at.isoformat() if challan.fetched_at else None,
            "is_payable": is_payable,
            "is_processing": status_upper == "OPS_PENDING",
        }
