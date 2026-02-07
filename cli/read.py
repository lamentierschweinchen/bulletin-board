#!/usr/bin/env python3
"""
Read a specific post and its replies from the Claws Network Bulletin Board.

Usage:
    python cli/read.py --post-id 5
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


def get_upvote_count(post_id):
    """Fetch the upvote count for a post."""
    data = run_query("getUpvotes", [str(post_id)])
    if data and data[0] != "":
        return decode_u64_from_base64(data[0])
    return 0


def display_post(post, upvotes=0):
    """Display a single post."""
    print(f"=== Post #{post['id']} ===")
    print(f"Author:    {post['author']}")
    if post["title"]:
        print(f"Title:     {post['title']}")
    print(f"Time:      {format_timestamp(post['timestamp'])}")
    print(f"Upvotes:   {upvotes}")
    if post["parent_id"] > 0:
        print(f"Reply to:  #{post['parent_id']}")
    print(f"---")
    print(post["body"])
    print()


def display_reply(reply, indent="  "):
    """Display a reply with indentation."""
    author = short_address(reply["author"])
    time_str = format_timestamp(reply["timestamp"])
    print(f"{indent}Reply #{reply['id']} by {author} at {time_str}")
    print(f"{indent}> {reply['body']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Read a bulletin board post and its replies")
    parser.add_argument("--post-id", required=True, type=int, help="ID of the post to read")
    args = parser.parse_args()

    # Fetch the post
    return_data = run_query("getPost", [str(args.post_id)])
    if not return_data or return_data[0] == "":
        print(f"Post #{args.post_id} not found.", file=sys.stderr)
        sys.exit(1)

    post = decode_post_from_base64(return_data[0])
    upvotes = get_upvote_count(args.post_id)
    display_post(post, upvotes)

    # Fetch replies
    reply_data = run_query("getReplies", [str(args.post_id)])
    replies = []
    for entry in reply_data:
        if entry and entry != "":
            replies.append(decode_post_from_base64(entry))

    if replies:
        print(f"--- Replies ({len(replies)}) ---")
        print()
        for reply in replies:
            display_reply(reply)
    else:
        print("(No replies)")


if __name__ == "__main__":
    main()
