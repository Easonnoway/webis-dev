import argparse
import sys
import os
from webis.core.pipeline import Pipeline
from webis.plugins.processors.html_fetcher_plugin import HTMLFetcherPlugin
from webis.plugins.processors.html_cleaner_plugin import HTMLCleanerPlugin
# Import other plugins as needed

def main():
    parser = argparse.ArgumentParser(description="Webis CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a URL")
    crawl_parser.add_argument("url", help="URL to crawl")
    crawl_parser.add_argument("--output", "-o", help="Output file", default=None)

    # extract command
    extract_parser = subparsers.add_parser("extract", help="Extract content from a file")
    extract_parser.add_argument("file", help="File to extract from")

    args = parser.parse_args()

    if args.command == "crawl":
        run_crawl(args.url, args.output)
    elif args.command == "extract":
        run_extract(args.file)
    else:
        parser.print_help()

def run_crawl(url: str, output: str = None):
    print(f"Crawling {url}...")
    pipeline = Pipeline()
    pipeline.add_plugin(HTMLFetcherPlugin())
    pipeline.add_plugin(HTMLCleanerPlugin())
    
    result = pipeline.run({"url": url})
    
    content = result.get("cleaned_html") or result.get("html")
    if output:
        with open(output, "w") as f:
            f.write(content)
        print(f"Saved to {output}")
    else:
        print(content[:500] + "..." if content else "No content")

def run_extract(file_path: str):
    print(f"Extracting from {file_path}...")
    # Determine file type and use appropriate processor
    # For now, just print a placeholder
    print("Extraction logic not fully implemented in CLI yet.")

if __name__ == "__main__":
    main()
