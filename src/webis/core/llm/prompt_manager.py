import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """
    Represents a prompt template with versioning.
    """
    name: str
    version: str
    template: str
    input_variables: List[str]
    description: Optional[str] = None
    examples: List[Dict[str, str]] = None # Few-shot examples
    
    def format(self, **kwargs) -> str:
        """Format the template with variables."""
        # Check for missing variables
        missing = [var for var in self.input_variables if var not in kwargs]
        if missing:
            raise ValueError(f"Missing input variables for prompt '{self.name}': {missing}")
            
        text = self.template
        
        # Append examples if present and not already in template
        if self.examples and "{examples}" not in text:
            example_text = "\n\nExamples:\n"
            for ex in self.examples:
                example_text += f"Input: {ex.get('input', '')}\nOutput: {ex.get('output', '')}\n\n"
            text += example_text
            
        return text.format(**kwargs)

class PromptManager:
    """
    Manages prompt templates and versions.
    """
    
    def __init__(self, prompt_dir: str = "./prompts"):
        self.prompt_dir = Path(prompt_dir)
        self._prompts: Dict[str, Dict[str, PromptTemplate]] = {} # name -> {version -> template}
        
        # Create directory if not exists
        if not self.prompt_dir.exists():
            self.prompt_dir.mkdir(parents=True, exist_ok=True)
            
        self.load_prompts()
        
    def load_prompts(self):
        """Load prompts from the prompt directory."""
        if not self.prompt_dir.exists():
            return
            
        for file_path in self.prompt_dir.glob("**/*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                name = data.get("name")
                version = data.get("version", "v1")
                template_str = data.get("template")
                input_variables = data.get("input_variables", [])
                description = data.get("description")
                
                if not name or not template_str:
                    logger.warning(f"Invalid prompt file: {file_path}")
                    continue
                    
                prompt = PromptTemplate(
                    name=name,
                    version=version,
                    template=template_str,
                    input_variables=input_variables,
                    description=description
                )
                
                if name not in self._prompts:
                    self._prompts[name] = {}
                    
                self._prompts[name][version] = prompt
                logger.debug(f"Loaded prompt: {name} ({version})")
                
            except Exception as e:
                logger.error(f"Failed to load prompt from {file_path}: {e}")

    def get_prompt(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        """
        Get a prompt template by name and version.
        If version is None, returns the latest version (lexicographically).
        """
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")
            
        versions = self._prompts[name]
        
        if version:
            if version not in versions:
                raise ValueError(f"Prompt version not found: {name} ({version})")
            return versions[version]
        
        # Default to latest version
        # Assuming versions are sortable strings like "v1", "v2", "1.0.0"
        latest_version = sorted(versions.keys())[-1]
        return versions[latest_version]

    def save_prompt(self, prompt: PromptTemplate):
        """Save a prompt template to disk."""
        file_path = self.prompt_dir / f"{prompt.name}_{prompt.version}.json"
        
        data = {
            "name": prompt.name,
            "version": prompt.version,
            "template": prompt.template,
            "input_variables": prompt.input_variables,
            "description": prompt.description
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        if prompt.name not in self._prompts:
            self._prompts[prompt.name] = {}
        self._prompts[prompt.name][prompt.version] = prompt
        logger.info(f"Saved prompt: {prompt.name} ({prompt.version})")

# Singleton instance
_default_prompt_manager: Optional[PromptManager] = None

def get_prompt_manager(prompt_dir: str = "./prompts") -> PromptManager:
    global _default_prompt_manager
    if _default_prompt_manager is None:
        _default_prompt_manager = PromptManager(prompt_dir)
    return _default_prompt_manager
