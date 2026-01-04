from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class SchemaValidatorPlugin(Plugin):
    """
    Plugin to validate and repair structured data against a schema.
    """
    def __init__(self, schema_model: Type[BaseModel]):
        self.schema_model = schema_model

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        data = kwargs.get("data") or context.get("data")
        if not data:
            return {"valid": False, "errors": ["No data provided"]}

        try:
            validated = self.schema_model.model_validate(data)
            return {"valid": True, "data": validated.model_dump()}
        except ValidationError as e:
            # Try to repair?
            # For now just return errors
            return {"valid": False, "errors": e.errors()}
