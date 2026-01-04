import argparse
import os
from typing import List
from webis.core.memory.retriever import HybridRetriever
from webis.core.memory.vector_store import VectorStore
from webis.core.llm.base import LLMFactory

def main():
    parser = argparse.ArgumentParser(description="Webis Chat")
    parser.add_argument("--collection", default="webis_knowledge", help="Vector store collection name")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="LLM model to use")
    args = parser.parse_args()

    print(f"Initializing Webis Chat (Collection: {args.collection}, Model: {args.model})...")
    
    # Initialize components
    try:
        vector_store = VectorStore(collection_name=args.collection)
        retriever = HybridRetriever(vector_store)
        llm = LLMFactory.create_llm(model_name=args.model)
    except Exception as e:
        print(f"Error initializing components: {e}")
        return

    print("Ready! Type 'exit' or 'quit' to stop.")
    print("-" * 50)

    while True:
        try:
            query = input("You: ")
            if query.lower() in ["exit", "quit"]:
                break
            
            if not query.strip():
                continue

            # 1. Retrieve relevant documents
            print("Thinking...")
            results = retriever.search(query, top_k=3)
            
            context_text = ""
            if results:
                context_text = "\n\n".join([f"Source {i+1}:\n{r.content}" for i, r in enumerate(results)])
            else:
                context_text = "No relevant information found in knowledge base."

            # 2. Generate answer
            prompt = f"""
            You are a helpful assistant for the Webis platform. 
            Use the following context to answer the user's question. 
            If the answer is not in the context, say you don't know, but try to be helpful.

            Context:
            {context_text}

            User Question: {query}

            Answer:
            """
            
            response = llm.generate(prompt)
            print(f"\nWebis: {response}\n")
            print("-" * 50)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
