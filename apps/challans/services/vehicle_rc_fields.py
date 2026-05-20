"""
ChallanPay find-challans response shape:

{
  "status": "success",
  "data": {
    "challans": [...],
    "vehicle": {
      "makerModel": "...",
      "vehicleCategory": "LGV",
      "rc": {
        "vehicleChasiNumber": "MA1RD2LYKR1D39744",
        "vehicleEngineNumber": "LYR1D50950",
        "ownerName": "MR IMRAN",
        ...
      }
    }
  }
}
"""


def extract_vehicle_from_raw(raw: dict | None) -> dict:
    """Resolve data.vehicle from combined fetch payload or find-challans body."""
    if not isinstance(raw, dict):
        return {}

    vehicle = raw.get("vehicle_rc")
    if isinstance(vehicle, dict) and vehicle:
        return vehicle

    find = raw.get("find_challans")
    if isinstance(find, dict):
        data = find.get("data")
        if isinstance(data, dict):
            nested = data.get("vehicle")
            if isinstance(nested, dict):
                return nested

    data = raw.get("data")
    if isinstance(data, dict):
        nested = data.get("vehicle")
        if isinstance(nested, dict):
            return nested

    return {}


def _rc_block(vehicle: dict) -> dict:
    rc = vehicle.get("rc")
    return rc if isinstance(rc, dict) else {}


def extract_chassis_engine(vehicle_payload: dict | None) -> tuple[str, str]:
    """
    Chassis and engine live under data.vehicle.rc in find-challans.
    ChallanPay field names use Chasi (not Chassis).
    """
    if not isinstance(vehicle_payload, dict):
        return "", ""

    rc = _rc_block(vehicle_payload)

    chassis = (
        rc.get("vehicleChasiNumber")
        or vehicle_payload.get("vehicleChasiNumber")
        or rc.get("vehicleChassisNumber")
        or vehicle_payload.get("vehicleChassisNumber")
        or ""
    )
    engine = (
        rc.get("vehicleEngineNumber")
        or vehicle_payload.get("vehicleEngineNumber")
        or ""
    )
    return str(chassis).strip()[:64], str(engine).strip()[:64]


def build_vehicle_metadata(raw: dict, *, subscriber_id, vehicle_id) -> dict:
    """Canonical vehicle + RC fields stored on challan rows and vehicles.external_metadata."""
    vehicle = extract_vehicle_from_raw(raw)
    rc = _rc_block(vehicle)
    chassis_number, engine_number = extract_chassis_engine(vehicle)

    return {
        "subscriber_id": subscriber_id,
        "vehicle_id": vehicle_id,
        "rc": rc,
        "maker_model": (vehicle.get("makerModel") or rc.get("makerModel") or "")[:128],
        "vehicle_category": (vehicle.get("vehicleCategory") or rc.get("vehicleCategory") or "")[:64],
        "chassis_number": chassis_number,
        "engine_number": engine_number,
        "owner_name": (rc.get("ownerName") or "")[:128],
    }
