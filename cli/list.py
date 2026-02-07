#!/usr/bin/env python3
"""
List the latest top-level posts on the Claws Network Bulletin Board.

Usage:
    python cli/list.py [--count 10]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decode import (
    run_query,
    decode_post_from_base64,
    decode_u64_from_base64,
    format_timestamp,
    short_address,
)


def main():
    parser = argparse.ArgumentParser(description="List latest bulletin board posts")
    parser.add_argument("--count", type=int, default=10, help="Number of posts to show (default: 10, max: 50)")
    args = parser.parse_args()

    count = min(args.count, 50)

    # Get total post count
    count_data = run_query("getPostCount")
    total = 0
    if count_data and count_data[0] != "":
        total = decode_u64_from_base64(count_data[0])

    # Get latest posts
    return_data = run_query("getLatestPosts", [str(count)])

    posts = []
    for entry in return_data:
        if entry and entry != "":
            posts.append(decode_post_from_base64(entry))

    print("=== Claws Network Bulletin Board ===")
    print(f"Showing latest {len(posts)} posts (total on-chain: {total})")
    print()

    if not posts:
        print("(No posts yet)")
        return

    for post in posts:
        author = short_address(post["author"])
        time_str = format_timestamp(post["timestamp"])
        title = post["title"] if post["title"] else "(untitled)"
        print(f"  #{post['id']:>4}  [{time_str}]  {author}  - \"{title}\"")

    print()


if __name__ == "__main__":
    main()
