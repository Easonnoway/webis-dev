"""
Pipeline engine for Webis.

Orchestrates the execution of source plugins, processors, and extractors
in a configurable workflow.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from webis.core.schema import (
    WebisDocument,
    StructuredResult,
    PipelineContext,
    DocumentStatus,
)
from webis.core.plugin import (
    SourcePlugin,
    ProcessorPlugin,
    ExtractorPlugin,
    PluginRegistry,
    get_default_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineStage:
    """Represents a single stage in the pipeline."""
    
    name: str
    plugin_name: str
    plugin_type: str  # "source", "processor", "extractor"
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Execution control
    enabled: bool = True
    continue_on_error: bool = False
    timeout_seconds: Optional[float] = None
    max_retries: int = 0
    condition: Optional[Callable[[PipelineContext, List[WebisDocument]], bool]] = None

    def should_run(self, context: PipelineContext, documents: List[WebisDocument]) -> bool:
        """Check if this stage should run based on condition."""
        if not self.enabled:
            return False
        if self.condition:
            try:
                return self.condition(context, documents)
            except Exception as e:
                logger.warning(f"Condition check failed for stage {self.name}: {e}")
                return False
        return True


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    
    success: bool
    documents: List[WebisDocument]
    structured_results: List[StructuredResult]
    context: PipelineContext
    
    # Timing
    started_at: float = 0.0
    completed_at: float = 0.0
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        return self.completed_at - self.started_at
    
    @property
    def document_count(self) -> int:
        return len(self.documents)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "document_count": self.document_count,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
            "tokens_used": self.context.total_tokens_used,
            "cost_usd": self.context.total_cost_usd,
        }


class Pipeline:
    """
    The main pipeline engine for Webis.
    
    Coordinates the flow of data through source plugins, processors,
    and extractors.
    
    Example:
        >>> pipe = Pipeline()
        >>> pipe.add_source("news_api")
        >>> pipe.add_processor("html_cleaner")
        >>> pipe.add_processor("chunker")
        >>> pipe.add_extractor("news_extractor")
        >>> result = pipe.run("Latest AI news")
    """
    
    def __init__(
        self,
        registry: Optional[PluginRegistry] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.registry = registry or get_default_registry()
        self.config = config or {}
        
        self._stages: List[PipelineStage] = []
        self._hooks: Dict[str, List[Callable]] = {
            "before_run": [],
            "after_run": [],
            "before_stage": [],
            "after_stage": [],
            "on_error": [],
        }
    
    def add_source(
        self, 
        plugin_name: str, 
        stage_name: Optional[str] = None,
        condition: Optional[Callable] = None,
        max_retries: int = 0,
        **config
    ) -> "Pipeline":
        """Add a source plugin stage."""
        self._stages.append(PipelineStage(
            name=stage_name or f"source_{plugin_name}",
            plugin_name=plugin_name,
            plugin_type="source",
            config=config,
            condition=condition,
            max_retries=max_retries,
        ))
        return self
    
    def add_processor(
        self, 
        plugin_name: str, 
        stage_name: Optional[str] = None,
        condition: Optional[Callable] = None,
        max_retries: int = 0,
        **config
    ) -> "Pipeline":
        """Add a processor plugin stage."""
        self._stages.append(PipelineStage(
            name=stage_name or f"process_{plugin_name}",
            plugin_name=plugin_name,
            plugin_type="processor",
            config=config,
            condition=condition,
            max_retries=max_retries,
        ))
        return self
    
    def add_extractor(
        self, 
        plugin_name: str, 
        stage_name: Optional[str] = None,
        condition: Optional[Callable] = None,
        max_retries: int = 0,
        **config
    ) -> "Pipeline":
        """Add an extractor plugin stage."""
        self._stages.append(PipelineStage(
            name=stage_name or f"extract_{plugin_name}",
            plugin_name=plugin_name,
            plugin_type="extractor",
            config=config,
            condition=condition,
            max_retries=max_retries,
        ))
        return self
    
    def add_hook(self, event: str, callback: Callable) -> "Pipeline":
        """
        Add a hook callback for pipeline events.
        
        Events:
        - before_run: Called before pipeline starts
        - after_run: Called after pipeline completes
        - before_stage: Called before each stage
        - after_stage: Called after each stage
        - on_error: Called when an error occurs
        """
        if event not in self._hooks:
            raise ValueError(f"Unknown event: {event}")
        self._hooks[event].append(callback)
        return self
    
    def _trigger_hooks(self, event: str, **kwargs) -> None:
        """Trigger all hooks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(**kwargs)
            except Exception as e:
                logger.warning(f"Hook error for {event}: {e}")
    
    def run(
        self,
        task: str,
        limit: int = 10,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> PipelineResult:
        """
        Execute the pipeline.
        
        Args:
            task: Natural language task description
            limit: Maximum documents to fetch
            output_dir: Output directory for results
            **kwargs: Additional parameters passed to plugins
            
        Returns:
            PipelineResult with documents and structured data
        """
        started_at = time.time()
        
        # Initialize context
        context = PipelineContext(
            task=task,
            config=self.config,
            output_dir=output_dir,
        )
        
        documents: List[WebisDocument] = []
        structured_results: List[StructuredResult] = []
        errors: List[Dict[str, Any]] = []
        
        self._trigger_hooks("before_run", context=context)
        
        try:
            for stage in self._stages:
                if not stage.should_run(context, documents):
                    logger.info(f"Skipping stage {stage.name} (condition not met or disabled)")
                    continue
                
                context.current_stage = stage.name
                self._trigger_hooks("before_stage", stage=stage, context=context)
                
                try:
                    # Define execution wrapper with retry logic
                    def execute_stage():
                        if stage.plugin_type == "source":
                            return self._run_source_stage(
                                stage, context, limit=limit, **kwargs
                            )
                        elif stage.plugin_type == "processor":
                            return self._run_processor_stage(
                                stage, documents, context, **kwargs
                            )
                        elif stage.plugin_type == "extractor":
                            return self._run_extractor_stage(
                                stage, documents, context, **kwargs
                            )
                        return None

                    # Apply retry decorator if max_retries > 0
                    if stage.max_retries > 0:
                        executor = retry(
                            stop=stop_after_attempt(stage.max_retries + 1),
                            wait=wait_exponential(multiplier=1, min=2, max=10),
                            reraise=True
                        )(execute_stage)
                    else:
                        executor = execute_stage

                    # Execute stage
                    result = executor()

                    # Update state based on result type
                    if stage.plugin_type == "source":
                        documents = result
                    elif stage.plugin_type == "processor":
                        documents = result
                    elif stage.plugin_type == "extractor" and result:
                        structured_results.append(result)
                    
                    self._trigger_hooks("after_stage", stage=stage, context=context)
                    
                except Exception as e:
                    error_info = {
                        "stage": stage.name,
                        "plugin": stage.plugin_name,
                        "error": str(e),
                    }
                    errors.append(error_info)
                    
                    self._trigger_hooks("on_error", error=error_info, context=context)
                    
                    if not stage.continue_on_error:
                        raise
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return PipelineResult(
                success=False,
                documents=documents,
                structured_results=structured_results,
                context=context,
                started_at=started_at,
                completed_at=time.time(),
                errors=errors,
            )
        
        self._trigger_hooks("after_run", context=context)
        
        return PipelineResult(
            success=True,
            documents=documents,
            structured_results=structured_results,
            context=context,
            started_at=started_at,
            completed_at=time.time(),
            errors=errors,
        )
    
    def _run_source_stage(
        self,
        stage: PipelineStage,
        context: PipelineContext,
        limit: int = 10,
        **kwargs
    ) -> List[WebisDocument]:
        """Execute a source plugin stage."""
        plugin = self.registry.get_source(stage.plugin_name)
        if not plugin:
            raise ValueError(f"Source plugin not found: {stage.plugin_name}")
        
        plugin.initialize(context)
        
        documents = []
        merged_kwargs = {**stage.config, **kwargs}
        
        for doc in plugin.fetch(context.task, limit=limit, context=context, **merged_kwargs):
            doc.status = DocumentStatus.COMPLETED
            doc.add_processing_step(stage.plugin_name, {"stage": stage.name})
            documents.append(doc)
            
            if len(documents) >= limit:
                break
        
        logger.info(f"Source '{stage.plugin_name}' fetched {len(documents)} documents")
        return documents
    
    def _run_processor_stage(
        self,
        stage: PipelineStage,
        documents: List[WebisDocument],
        context: PipelineContext,
        **kwargs
    ) -> List[WebisDocument]:
        """Execute a processor plugin stage."""
        plugin = self.registry.get_processor(stage.plugin_name)
        if not plugin:
            raise ValueError(f"Processor plugin not found: {stage.plugin_name}")
        
        plugin.initialize(context)
        
        merged_kwargs = {**stage.config, **kwargs}
        processed = plugin.process_batch(documents, context=context, **merged_kwargs)
        
        logger.info(
            f"Processor '{stage.plugin_name}' processed {len(documents)} -> {len(processed)} documents"
        )
        return processed
    
    def _run_extractor_stage(
        self,
        stage: PipelineStage,
        documents: List[WebisDocument],
        context: PipelineContext,
        **kwargs
    ) -> Optional[StructuredResult]:
        """Execute an extractor plugin stage."""
        plugin = self.registry.get_extractor(stage.plugin_name)
        if not plugin:
            raise ValueError(f"Extractor plugin not found: {stage.plugin_name}")
        
        if not documents:
            logger.warning(f"No documents to extract from in stage '{stage.name}'")
            return None
        
        plugin.initialize(context)
        
        merged_kwargs = {**stage.config, **kwargs}
        result = plugin.extract(documents, context=context, **merged_kwargs)
        
        logger.info(f"Extractor '{stage.plugin_name}' produced result: {result.schema_id}")
        return result
    
    @classmethod
    def from_config(cls, config: Dict[str, Any], registry: Optional[PluginRegistry] = None) -> "Pipeline":
        """
        Create a pipeline from a configuration dictionary.
        
        Example config:
            {
                "stages": [
                    {"type": "source", "plugin": "news_api", "config": {"api_key": "..."}},
                    {"type": "processor", "plugin": "html_cleaner"},
                    {"type": "extractor", "plugin": "news_extractor"}
                ]
            }
        """
        pipeline = cls(registry=registry, config=config)
        
        for stage_config in config.get("stages", []):
            stage_type = stage_config.get("type")
            plugin_name = stage_config.get("plugin")
            plugin_config = stage_config.get("config", {})
            stage_name = stage_config.get("name")
            
            if stage_type == "source":
                pipeline.add_source(plugin_name, stage_name=stage_name, **plugin_config)
            elif stage_type == "processor":
                pipeline.add_processor(plugin_name, stage_name=stage_name, **plugin_config)
            elif stage_type == "extractor":
                pipeline.add_extractor(plugin_name, stage_name=stage_name, **plugin_config)
        
        return pipeline
    
    @classmethod
    def from_preset(cls, preset_name: str, registry: Optional[PluginRegistry] = None) -> "Pipeline":
        """
        Create a pipeline from a preset configuration.
        
        Available presets:
        - "news_analyst": Fetch and analyze news articles
        - "research_assistant": Fetch and summarize academic papers
        - "web_scraper": General web scraping and cleaning
        """
        presets = {
            "news_analyst": {
                "stages": [
                    {"type": "source", "plugin": "news_search"},
                    {"type": "processor", "plugin": "html_cleaner"},
                    {"type": "processor", "plugin": "chunker"},
                    {"type": "extractor", "plugin": "news_extractor"},
                ]
            },
            "research_assistant": {
                "stages": [
                    {"type": "source", "plugin": "semantic_scholar"},
                    {"type": "processor", "plugin": "pdf_extractor"},
                    {"type": "processor", "plugin": "chunker"},
                    {"type": "extractor", "plugin": "paper_summarizer"},
                ]
            },
            "web_scraper": {
                "stages": [
                    {"type": "source", "plugin": "web_search"},
                    {"type": "processor", "plugin": "html_cleaner"},
                ]
            },
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
        
        return cls.from_config(presets[preset_name], registry=registry)


__all__ = [
    "PipelineStage",
    "PipelineResult",
    "Pipeline",
]
