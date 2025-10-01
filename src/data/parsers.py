"""Parsing utilities for normalising KMA API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping

from src.utils.logger_config import configure_logger


_logger = configure_logger(__name__)


def _parse_datetime(base_date: str, base_time: str) -> datetime:
    naive = datetime.strptime(f"{base_date}{base_time}", "%Y%m%d%H%M")
    return naive.replace(tzinfo=timezone.utc)


def extract_measurements(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Transform the raw KMA payload into a flat list of rows."""

    response_body = payload.get("response", {}).get("body", {})
    items: Iterable[Mapping[str, Any]] = response_body.get("items", [])
    base_date = response_body.get("baseDate")
    base_time = response_body.get("baseTime")

    if not base_date or not base_time:
        raise ValueError("KMA payload missing base date/time metadata")

    observed_at = _parse_datetime(base_date, base_time)

    rows: List[Dict[str, Any]] = []
    for item in items:
        row = {
            "station_id": item.get("stationId"),
            "observed_at": observed_at,
            "category": item.get("category"),
            "value": item.get("obsrValue"),
            "unit": item.get("unit", ""),
            "created_at": datetime.now(tz=timezone.utc),
        }
        rows.append(row)

    _logger.info("Parsed KMA payload", extra={"rows": len(rows)})
    return rows


def parse_asos_raw(raw_data: str) -> List[Dict[str, Any]]:
    """Parse ASOS (지상관측) raw data from KMA API (supports XML and text formats)"""
    try:
        # Try XML parsing first
        if raw_data.strip().startswith('<?xml'):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(raw_data)
            items = root.findall('.//item')

            parsed_data = []
            for item in items:
                station_id = item.find('stnId')
                tm = item.find('tm')

                # 기온 (temperature)
                ta = item.find('ta')
                # 풍속 (wind speed)
                ws = item.find('ws')
                # 습도 (humidity)
                hm = item.find('hm')
                # 기압 (pressure)
                pa = item.find('pa')
                # 강수량 (rainfall)
                rn = item.find('rn')
                # 풍향 (wind direction)
                wd = item.find('wd')
                # 이슬점 (dew point)
                td = item.find('td')
                # 운량 (cloud amount)
                ca = item.find('ca')
                # 시정 (visibility)
                vs = item.find('vs')
                # 일조 (sunshine)
                ss = item.find('ss')

                if station_id is not None and tm is not None:
                    parsed_data.append({
                        "station_id": station_id.text,
                        "observed_at": _parse_datetime_from_line(tm.text) if tm.text else datetime.now(tz=timezone.utc),
                        "category": "asos",
                        "temperature": ta.text if ta is not None and ta.text else None,
                        "wind_speed": ws.text if ws is not None and ws.text else None,
                        "humidity": hm.text if hm is not None and hm.text else None,
                        "pressure": pa.text if pa is not None and pa.text else None,
                        "rainfall": rn.text if rn is not None and rn.text else None,
                        "wind_direction": wd.text if wd is not None and wd.text else None,
                        "dew_point": td.text if td is not None and td.text else None,
                        "cloud_amount": ca.text if ca is not None and ca.text else None,
                        "visibility": vs.text if vs is not None and vs.text else None,
                        "sunshine": ss.text if ss is not None and ss.text else None,
                        "created_at": datetime.now(tz=timezone.utc),
                    })

            _logger.info(f"Parsed ASOS data: {len(parsed_data)} records")
            return parsed_data

        # Fallback to text parsing
        lines = raw_data.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]

        parsed_data = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 3:
                parsed_data.append({
                    "station_id": parts[1] if len(parts) > 1 else "unknown",
                    "observed_at": _parse_datetime_from_line(parts[0]) if parts[0] else datetime.now(tz=timezone.utc),
                    "category": "asos",
                    "value": parts[2] if len(parts) > 2 else None,
                    "unit": "",
                    "created_at": datetime.now(tz=timezone.utc),
                    "raw_line": line
                })

        _logger.info(f"Parsed ASOS data: {len(parsed_data)} records")
        return parsed_data
    except Exception as e:
        _logger.error(f"Failed to parse ASOS data: {e}")
        return []


def parse_pm10_raw(raw_data: str) -> List[Dict[str, Any]]:
    """Parse PM10 (황사) raw data from KMA API (supports XML and text formats)"""
    try:
        # Try XML parsing first
        if raw_data.strip().startswith('<?xml'):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(raw_data)
            items = root.findall('.//item')

            parsed_data = []
            for item in items:
                station_id = item.find('stnId')
                msr_dt = item.find('msrDt')
                msr_val = item.find('msrVal')

                if station_id is not None and msr_dt is not None:
                    pm10_value = None
                    if msr_val is not None and msr_val.text:
                        try:
                            pm10_value = float(msr_val.text)
                        except ValueError:
                            pm10_value = None

                    parsed_data.append({
                        "station_id": station_id.text,
                        "observed_at": _parse_datetime_from_line(msr_dt.text) if msr_dt.text else datetime.now(tz=timezone.utc),
                        "category": "pm10",
                        "value": pm10_value,
                        "unit": "μg/m³",
                        "created_at": datetime.now(tz=timezone.utc),
                    })

            _logger.info(f"Parsed PM10 data: {len(parsed_data)} records")
            return parsed_data

        # Fallback to CSV parsing
        lines = raw_data.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]

        parsed_data = []
        for line in data_lines:
            parts = line.split(',')
            if len(parts) >= 3:
                datetime_str = parts[0].strip() if parts[0] else ""
                station_id = parts[1].strip() if len(parts) > 1 else "unknown"
                pm10_value = parts[2].strip() if len(parts) > 2 else None

                try:
                    if pm10_value and pm10_value.isdigit():
                        pm10_value = int(pm10_value)
                    else:
                        pm10_value = None
                except:
                    pm10_value = None

                parsed_data.append({
                    "station_id": station_id,
                    "observed_at": _parse_datetime_from_line(datetime_str) if datetime_str else datetime.now(tz=timezone.utc),
                    "category": "pm10",
                    "value": pm10_value,
                    "unit": "μg/m³",
                    "created_at": datetime.now(tz=timezone.utc),
                    "raw_line": line
                })

        _logger.info(f"Parsed PM10 data: {len(parsed_data)} records")
        return parsed_data
    except Exception as e:
        _logger.error(f"Failed to parse PM10 data: {e}")
        return []




def _parse_datetime_from_line(datetime_str: str) -> datetime:
    """Parse datetime from KMA API line format (YYYYMMDDHHMM)"""
    try:
        if len(datetime_str) == 12:  # YYYYMMDDHHMM
            return datetime.strptime(datetime_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        elif len(datetime_str) == 10:  # YYMMDDHHMM
            return datetime.strptime(f"20{datetime_str}", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        else:
            return datetime.now(tz=timezone.utc)
    except ValueError:
        return datetime.now(tz=timezone.utc)


__all__ = ["extract_measurements", "parse_asos_raw", "parse_pm10_raw"]