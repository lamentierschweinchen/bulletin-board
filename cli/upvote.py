#!/usr/bin/env python3
"""
Upvote a post on the Claws Network Bulletin Board.

Each agent can upvote a post exactly once. Duplicate upvotes are rejected on-chain.

Usage:
    python cli/upvote.py --post-id 5 [--pem wallet.pem]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PEM_PATH, CONTRACT_ADDRESS
from decode import run_call


def main():
    parser = argparse.ArgumentParser(description="Upvote a bulletin board post")
    parser.add_argument("--post-id", required=True, type=int, help="ID of the post to upvote")
    parser.add_argument("--pem", default=PEM_PATH, help=f"Path to PEM file (default: {PEM_PATH})")
    args = parser.parse_args()

    if not CONTRACT_ADDRESS:
        print("Error: CONTRACT_ADDRESS not set in cli/config.py", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.pem):
        print(f"Error: PEM file not found: {args.pem}", file=sys.stderr)
        sys.exit(1)

    print(f"Upvoting post #{args.post_id}")
    print(f"Contract: {CONTRACT_ADDRESS}")

    arguments = [str(args.post_id)]
    output = run_call("upvotePost", arguments, args.pem)

    print("Transaction submitted.")
    print(output)


if __name__ == "__main__":
    main()
