from typing import List, Dict, Any
from collections import defaultdict
from webis.core.schema import WebisDocument

class FusionEngine:
    """
    Merges information from multiple documents to create a unified view.
    Handles entity resolution and conflict management.
    """
    
    def fuse_documents(self, docs: List[WebisDocument], entity_key: str = "entities") -> Dict[str, Any]:
        """
        Fuses extracted entities from multiple documents.
        
        Args:
            docs: List of processed documents.
            entity_key: The key in doc.meta.extra where entities are stored.
            
        Returns:
            A dictionary of merged entities.
        """
        merged_entities = defaultdict(lambda: {"mentions": 0, "sources": set(), "attributes": {}})
        
        for doc in docs:
            entities = doc.meta.extra.get(entity_key, [])
            # Assuming entities is a list of dicts like [{'name': 'Apple', 'type': 'Org', ...}]
            for entity in entities:
                name = entity.get("name")
                if not name:
                    continue
                
                # Simple normalization
                norm_name = name.lower().strip()
                
                entry = merged_entities[norm_name]
                entry["mentions"] += 1
                entry["sources"].add(doc.id)
                
                # Merge attributes (simple overwrite or list append strategy)
                for k, v in entity.items():
                    if k == "name": 
                        entry["name"] = name # Keep original casing of last seen
                        continue
                        
                    if k not in entry["attributes"]:
                        entry["attributes"][k] = set()
                    
                    # Store all values seen for this attribute
                    entry["attributes"][k].add(str(v))

        # Convert sets back to lists for JSON serialization
        result = []
        for norm_name, data in merged_entities.items():
            final_entity = {
                "name": data.get("name", norm_name),
                "mentions": data["mentions"],
                "sources": list(data["sources"])
            }
            for k, v_set in data["attributes"].items():
                final_entity[k] = list(v_set)
            result.append(final_entity)
            
        return {"fused_entities": result, "doc_count": len(docs)}
