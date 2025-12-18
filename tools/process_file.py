#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webis single-file processing CLI (moved under tools/).

Usage (from project root):
  python tools/process_file.py <file_path>
"""

from __future__ import annotations

import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from file_processor import UnifiedFileProcessor, extract_text_from_file  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("Webis - Unified File Processing Tool")
        print("=" * 50)
        print("Usage: python tools/process_file.py <file_path>")
        print()

        processor = UnifiedFileProcessor()
        print("Supported file types:")
        for category, exts in processor.get_supported_extensions().items():
            print(f"  {category}: {', '.join(exts)}")
        print()
        print("Examples:")
        print("  python tools/process_file.py tools/data/pdf/example.pdf")
        print("  python tools/process_file.py data/some_file.html")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isabs(file_path) and not os.path.exists(file_path):
        search_paths = [
            file_path,
            os.path.join(os.path.dirname(TOOLS_DIR), "tools", "data", file_path),
            os.path.join(os.path.dirname(TOOLS_DIR), "data", file_path),
            os.path.join(os.path.dirname(TOOLS_DIR), "tools", "processors", file_path),
        ]

        for search_path in search_paths:
            if os.path.exists(search_path):
                file_path = search_path
                break
        else:
            print(f"Error: File not found {sys.argv[1]}")
            sys.exit(1)

    print(f"Processing file: {file_path}")
    print("-" * 50)

    result = extract_text_from_file(file_path)

    if result["success"]:
        print("✓ Processing successful")
        print(f"File type: {result['file_type']}")
        print(f"Text length: {len(result['text'])} characters")
        print()
        print("Extracted text content:")
        print("=" * 50)
        print(result["text"])
    else:
        print(f"✗ Processing failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

