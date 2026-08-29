import sys
from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from subjective_abstract_data_source_package import SubjectiveDataSource

from trading_contracts.plugin_support import icon_for


class SubjectiveSymbolMonitorSequenceDataSource(SubjectiveDataSource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.window = max(1, int(self._connection.get("window", 20)))
        self._windows = defaultdict(lambda: deque(maxlen=self.window))

    @classmethod
    def connection_schema(cls):
        return {"window": {"type": "int", "label": "SMA Window", "default": 20, "min": 1}}

    @classmethod
    def request_schema(cls):
        return {"event": {"type": "object", "label": "Market Event"}, "events": {"type": "array", "label": "Market Events"}}

    @classmethod
    def output_schema(cls):
        return {"symbol": {"type": "text", "label": "Symbol"}, "market": {"type": "object", "label": "Latest Market Event"}, "sequence": {"type": "array", "label": "Price Window"}, "sma": {"type": "text", "label": "SMA"}, "ready": {"type": "bool", "label": "Window Ready"}, "error": {"type": "text", "label": "Error"}}

    @classmethod
    def icon(cls):
        return icon_for(__file__)

    def run(self, request):
        request = request or {}
        events = request.get("events") or ([request["event"]] if request.get("event") else [])
        latest = None
        try:
            for event in events:
                event = event.get("event", event) if isinstance(event, dict) else event
                symbol = str(event.get("symbol", "")).upper()
                value = str(event.get("last", event.get("close", "")))
                if not symbol or not value:
                    continue
                Decimal(value)
                self._windows[symbol].append(value)
                latest = event
            if not latest:
                return {"symbol": "", "market": None, "sequence": [], "sma": "", "ready": False, "error": "market event required"}
            values = self._windows[str(latest["symbol"]).upper()]
            ready = len(values) >= self.window
            sma = format(sum(Decimal(value) for value in values) / len(values), "f") if ready else ""
            return {"symbol": str(latest["symbol"]).upper(), "market": latest, "sequence": list(values), "sma": sma, "ready": ready, "error": ""}
        except (InvalidOperation, TypeError, ValueError) as exc:
            return {"symbol": "", "market": latest, "sequence": [], "sma": "", "ready": False, "error": str(exc)}
