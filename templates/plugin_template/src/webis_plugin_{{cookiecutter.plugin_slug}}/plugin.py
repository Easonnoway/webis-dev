from typing import Any, Dict
from webis.plugin_sdk import ProcessorPlugin, WebisDocument, PipelineContext, get_logger

logger = get_logger("{{cookiecutter.plugin_slug}}")

class {{cookiecutter.plugin_class_name}}(ProcessorPlugin):
    """
    {{cookiecutter.plugin_description}}
    """
    name = "{{cookiecutter.plugin_slug}}"

    def __init__(self, config_param: str = "default"):
        self.config_param = config_param

    def process(self, doc: WebisDocument, context: PipelineContext) -> WebisDocument:
        logger.info(f"Processing document {doc.id} with param {self.config_param}")
        
        # TODO: Implement your processing logic here
        # doc.content = doc.content.upper()
        
        return doc
