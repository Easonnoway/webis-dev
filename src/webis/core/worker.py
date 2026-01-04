import logging
from typing import Dict, Any, List
from webis.core.celery_app import celery_app
from webis.core.pipeline import Pipeline
from webis.core.schema import PipelineContext

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def run_pipeline_task(self, query: str, pipeline_config: Dict[str, Any]):
    """
    Celery task to run the Webis pipeline.
    """
    task_id = self.request.id
    logger.info(f"Starting pipeline task {task_id} for query: {query}")
    
    self.update_state(state='PROCESSING', meta={'progress': 0, 'status': 'Initializing'})
    
    try:
        # Initialize pipeline
        pipeline = Pipeline()
        
        # Configure pipeline from config dictionary
        stages = pipeline_config.get("stages", [])
        for stage in stages:
            stage_type = stage.get("type")
            plugin_name = stage.get("plugin")
            config = stage.get("config", {})
            name = stage.get("name")
            
            if stage_type == "source":
                pipeline.add_source(plugin_name, stage_name=name, **config)
            elif stage_type == "processor":
                pipeline.add_processor(plugin_name, stage_name=name, **config)
            elif stage_type == "extractor":
                pipeline.add_extractor(plugin_name, stage_name=name, **config)
            else:
                logger.warning(f"Unknown stage type: {stage_type}")

        # If no source is defined, add a default one or fail
        # For now, we assume the config is valid or the pipeline handles it
        
        self.update_state(state='PROCESSING', meta={'progress': 10, 'status': 'Running Pipeline'})
        
        # Run the pipeline
        # We pass the query as the 'task'
        result = pipeline.run(task=query, **pipeline_config.get("run_params", {}))
        
        result_summary = result.to_dict()
        
        if result.success:
            return {"status": "completed", "result": result_summary}
        else:
            return {"status": "failed", "result": result_summary, "error": "Pipeline execution failed"}
        
    except Exception as e:
        logger.error(f"Pipeline task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
