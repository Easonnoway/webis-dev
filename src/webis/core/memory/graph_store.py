from typing import List, Dict, Any, Optional
import os
from neo4j import GraphDatabase

class GraphStore:
    """
    Graph database interface using Neo4j.
    """
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None

    def connect(self):
        if not self.driver:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        if self.driver:
            self.driver.close()

    def add_entity(self, label: str, properties: Dict[str, Any]):
        """Add a node to the graph."""
        self.connect()
        query = f"MERGE (n:{label} {{id: $id}}) SET n += $props"
        if "id" not in properties:
            raise ValueError("Entity must have an 'id' property")
            
        with self.driver.session() as session:
            session.run(query, id=properties["id"], props=properties)

    def add_relation(self, from_id: str, to_id: str, relation_type: str, properties: Dict[str, Any] = None):
        """Add a relationship between two nodes."""
        self.connect()
        props_str = ""
        if properties:
            # Simple property serialization for Cypher
            # In production, use parameters
            pass 
            
        query = f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        MERGE (a)-[r:{relation_type}]->(b)
        """
        if properties:
            query += " SET r += $props"
            
        with self.driver.session() as session:
            session.run(query, from_id=from_id, to_id=to_id, props=properties or {})

    def query(self, cypher: str, parameters: Dict[str, Any] = None):
        """Execute a raw Cypher query."""
        self.connect()
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]
