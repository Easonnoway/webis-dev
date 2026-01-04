from locust import HttpUser, task, between
import json
import random

class WebisUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def ingest_document(self):
        """
        Simulate submitting an ingestion task.
        """
        payload = {
            "query": f"Test Query {random.randint(1, 1000)}",
            "pipeline_preset": "default"
        }
        self.client.post("/api/v1/ingest", json=payload)

    @task(1)
    def query_rag(self):
        """
        Simulate a RAG query.
        """
        query = f"What is AI? {random.randint(1, 100)}"
        self.client.post(f"/api/v1/query?q={query}")

    @task(2)
    def check_health(self):
        self.client.get("/health")
