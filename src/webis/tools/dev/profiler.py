import time
from typing import Dict, List, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProfileEvent:
    name: str
    start_time: float
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

class PipelineProfiler:
    """
    Profiler for analyzing pipeline performance.
    """
    def __init__(self):
        self.events: List[ProfileEvent] = []
        self._active_events: Dict[str, ProfileEvent] = {}

    def start_event(self, name: str, metadata: Dict[str, Any] = None):
        event = ProfileEvent(name=name, start_time=time.time(), metadata=metadata or {})
        self._active_events[name] = event
        return event

    def stop_event(self, name: str):
        if name in self._active_events:
            event = self._active_events.pop(name)
            event.end_time = time.time()
            self.events.append(event)
            return event
        else:
            logger.warning(f"Event {name} not found in active events")

    def get_summary(self) -> Dict[str, Any]:
        total_duration = sum(e.duration for e in self.events)
        summary = {
            "total_duration": total_duration,
            "events": []
        }
        
        for event in self.events:
            summary["events"].append({
                "name": event.name,
                "duration": event.duration,
                "percentage": (event.duration / total_duration * 100) if total_duration > 0 else 0
            })
            
        return summary

    def print_report(self):
        summary = self.get_summary()
        print("\n=== Pipeline Profile Report ===")
        print(f"Total Duration: {summary['total_duration']:.4f}s")
        print("-" * 40)
        print(f"{'Event':<30} | {'Duration':<10} | {'%':<5}")
        print("-" * 40)
        for event in summary["events"]:
            print(f"{event['name']:<30} | {event['duration']:.4f}s   | {event['percentage']:.1f}%")
        print("===============================\n")
