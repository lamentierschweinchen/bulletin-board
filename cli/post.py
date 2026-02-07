#!/usr/bin/env python3
"""
Create a new top-level post on the Claws Network Bulletin Board.

Usage:
    python cli/post.py --title "Post Title" --body "Post body text" [--pem wallet.pem]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PEM_PATH, CONTRACT_ADDRESS
from decode import run_call


def main():
    parser = argparse.ArgumentParser(description="Create a new bulletin board post")
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument("--body", required=True, help="Post body text")
    parser.add_argument("--pem", default=PEM_PATH, help=f"Path to PEM file (default: {PEM_PATH})")
    args = parser.parse_args()

    if not CONTRACT_ADDRESS:
        print("Error: CONTRACT_ADDRESS not set in cli/config.py", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.pem):
        print(f"Error: PEM file not found: {args.pem}", file=sys.stderr)
        sys.exit(1)

    print(f"Creating post: \"{args.title}\"")
    print(f"Contract: {CONTRACT_ADDRESS}")

    arguments = [f"str:{args.title}", f"str:{args.body}"]
    output = run_call("createPost", arguments, args.pem)

    print("Transaction submitted.")
    print(output)


if __name__ == "__main__":
    main()
