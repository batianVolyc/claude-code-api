#!/usr/bin/env python3
"""
Generate secure API keys for Claude Code API Gateway
"""

import secrets
import sys
import argparse


def generate_api_key(prefix: str = "cc", length: int = 32) -> str:
    """Generate a secure API key."""
    random_part = secrets.token_hex(length)
    return f"{prefix}_{random_part}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate secure API keys for Claude Code API Gateway"
    )
    parser.add_argument(
        "-n", "--number",
        type=int,
        default=1,
        help="Number of API keys to generate (default: 1)"
    )
    parser.add_argument(
        "-p", "--prefix",
        type=str,
        default="cc",
        help="Prefix for API keys (default: cc)"
    )
    parser.add_argument(
        "-l", "--length",
        type=int,
        default=32,
        help="Length of random part in bytes (default: 32)"
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Output in .env format"
    )
    
    args = parser.parse_args()
    
    keys = [generate_api_key(args.prefix, args.length) for _ in range(args.number)]
    
    if args.env:
        print(f"# Generated API keys for Claude Code API Gateway")
        print(f"REQUIRE_AUTH=true")
        print(f"API_KEYS={','.join(keys)}")
    else:
        print("Generated API Keys:")
        print("-" * 50)
        for i, key in enumerate(keys, 1):
            print(f"Key {i}: {key}")
        print("-" * 50)
        print("\nTo use these keys, add them to your .env file:")
        print(f"API_KEYS={','.join(keys)}")


if __name__ == "__main__":
    main()