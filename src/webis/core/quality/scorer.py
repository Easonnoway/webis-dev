from typing import Any, Dict, List
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class QualityScorerPlugin(Plugin):
    """
    Plugin to calculate data quality score.
    """
    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        data = kwargs.get("data") or context.get("data")
        if not data:
            return {"score": 0.0}

        # Simple completeness score
        if isinstance(data, dict):
            total_fields = len(data)
            filled_fields = sum(1 for v in data.values() if v)
            completeness = filled_fields / total_fields if total_fields > 0 else 0.0
        else:
            completeness = 1.0 if data else 0.0
        
        return {"score": completeness, "completeness": completeness}
