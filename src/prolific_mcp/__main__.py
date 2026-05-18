import argparse

from prolific_mcp.server import mcp


def main() -> None:
    parser = argparse.ArgumentParser(prog="prolific-mcp")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Serve over streamable HTTP instead of stdio (useful for local dev).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host to bind (only with --http). Default: 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="HTTP port to bind (only with --http). Default: 8765.",
    )
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
