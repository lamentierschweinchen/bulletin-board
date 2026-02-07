"""
Shared decoding utilities for Claws Network Bulletin Board CLI.

Handles:
- Parsing clawpy contract query JSON output
- Decoding binary-encoded Post structs (MultiversX nested encoding)
- Bech32 address conversion (raw 32-byte pubkey -> claw1... address)
"""

import base64
import json
import struct
import subprocess
import sys

try:
    import bech32
except ImportError:
    print("Missing dependency: pip install bech32", file=sys.stderr)
    sys.exit(1)

from config import CONTRACT_ADDRESS, PROXY_URL, CLAWPY


def run_query(function, arguments=None):
    """Execute a clawpy contract query and return the returnData list (base64 strings)."""
    if not CONTRACT_ADDRESS:
        print("Error: CONTRACT_ADDRESS not set in cli/config.py", file=sys.stderr)
        sys.exit(1)

    cmd = [
        CLAWPY, "contract", "query", CONTRACT_ADDRESS,
        "--proxy", PROXY_URL,
        "--function", function,
    ]
    if arguments:
        cmd.append("--arguments")
        cmd.extend(arguments)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Query failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # clawpy query output is JSON with a returnData field (list of base64 values)
    try:
        output = json.loads(result.stdout)
        return output.get("returnData", [])
    except json.JSONDecodeError:
        # Some versions output line-based format; try to parse returnData from lines
        lines = result.stdout.strip().splitlines()
        # Look for base64-like values
        return [line.strip() for line in lines if line.strip()]


def run_call(function, arguments, pem_path):
    """Execute a clawpy contract call (write transaction) and return stdout."""
    from config import GAS_LIMIT_CALL, GAS_PRICE, CHAIN_ID

    if not CONTRACT_ADDRESS:
        print("Error: CONTRACT_ADDRESS not set in cli/config.py", file=sys.stderr)
        sys.exit(1)

    cmd = [
        CLAWPY, "contract", "call", CONTRACT_ADDRESS,
        "--proxy", PROXY_URL,
        "--chain", CHAIN_ID,
        "--function", function,
        "--gas-limit", str(GAS_LIMIT_CALL),
        "--gas-price", str(GAS_PRICE),
        "--recall-nonce",
        "--pem", pem_path,
        "--send",
    ]
    if arguments:
        cmd.append("--arguments")
        cmd.extend(arguments)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Transaction failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    return result.stdout


def pubkey_to_bech32(pubkey_bytes):
    """Convert a 32-byte public key to a bech32 claw1... address."""
    converted = bech32.convertbits(list(pubkey_bytes), 8, 5)
    if converted is None:
        return "<invalid-address>"
    return bech32.bech32_encode("claw", converted)


def decode_u64(data, offset):
    """Read a big-endian u64 from bytes at offset. Returns (value, new_offset)."""
    val = struct.unpack_from(">Q", data, offset)[0]
    return val, offset + 8


def decode_u32(data, offset):
    """Read a big-endian u32 from bytes at offset. Returns (value, new_offset)."""
    val = struct.unpack_from(">I", data, offset)[0]
    return val, offset + 4


def decode_managed_buffer(data, offset):
    """Decode a length-prefixed ManagedBuffer. Returns (string, new_offset)."""
    length, offset = decode_u32(data, offset)
    buf = data[offset:offset + length]
    return buf.decode("utf-8", errors="replace"), offset + length


def decode_managed_address(data, offset):
    """Decode a 32-byte ManagedAddress. Returns (bech32_str, new_offset)."""
    raw = data[offset:offset + 32]
    return pubkey_to_bech32(raw), offset + 32


def decode_post(data):
    """
    Decode a single Post struct from its binary (nested-encoded) representation.

    Layout:
      id:        u64        (8 bytes, big-endian)
      author:    Address    (32 bytes)
      title:     Buffer     (4-byte u32 length + N bytes)
      body:      Buffer     (4-byte u32 length + N bytes)
      timestamp: u64        (8 bytes, big-endian)
      parent_id: u64        (8 bytes, big-endian)

    Returns a dict with decoded fields.
    """
    offset = 0
    post_id, offset = decode_u64(data, offset)
    author, offset = decode_managed_address(data, offset)
    title, offset = decode_managed_buffer(data, offset)
    body, offset = decode_managed_buffer(data, offset)
    timestamp, offset = decode_u64(data, offset)
    parent_id, offset = decode_u64(data, offset)

    return {
        "id": post_id,
        "author": author,
        "title": title,
        "body": body,
        "timestamp": timestamp,
        "parent_id": parent_id,
    }


def decode_post_from_base64(b64_str):
    """Decode a Post from a base64-encoded return data entry."""
    raw = base64.b64decode(b64_str)
    return decode_post(raw)


def decode_u64_from_base64(b64_str):
    """Decode a single u64 from a base64-encoded return data entry."""
    raw = base64.b64decode(b64_str)
    if len(raw) == 0:
        return 0
    # MultiversX encodes small integers with minimal bytes (no leading zeros)
    return int.from_bytes(raw, byteorder="big")


def format_timestamp(ts):
    """Format a Unix timestamp for display."""
    from datetime import datetime, timezone
    if ts == 0:
        return "N/A"
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def short_address(addr):
    """Shorten a bech32 address for display: claw1abc...xyz"""
    if len(addr) > 16:
        return f"{addr[:10]}...{addr[-4:]}"
    return addr
