import time
import random
from webis.core.schema import WebisDocument, DocumentType
from webis.core.observability import tracer

# Mock processing function to benchmark
@tracer.trace("process_document")
def process_document(doc: WebisDocument):
    # Simulate CPU work
    time.sleep(random.uniform(0.01, 0.05))
    return doc

def run_benchmark(num_docs: int = 100):
    print(f"Starting benchmark with {num_docs} documents...")
    
    docs = [
        WebisDocument(content=f"Content {i}", doc_type=DocumentType.TEXT)
        for i in range(num_docs)
    ]
    
    start_time = time.time()
    
    for doc in docs:
        process_document(doc)
        
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = (total_time / num_docs) * 1000
    
    print(f"Benchmark completed.")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per doc: {avg_time:.2f}ms")
    print(f"Throughput: {num_docs / total_time:.2f} docs/s")

if __name__ == "__main__":
    run_benchmark()
