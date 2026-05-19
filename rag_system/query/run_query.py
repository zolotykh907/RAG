import argparse

from rag_system.shared.data_base import FaissDB
from rag_system.shared.my_config import Config
from rag_system.query.query import Query


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single search query against the indexed corpus.")
    parser.add_argument("query", help="Search query string.")
    parser.add_argument("--k", type=int, default=None, help="Number of results (overrides config).")
    parser.add_argument("--no-rerank", action="store_true", help="Disable reranking.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = Config("rag_system/query/config.yaml")
    if args.k is not None:
        setattr(config, "k", args.k)  # noqa: B010
    if args.no_rerank:
        setattr(config, "rerank_enabled", False)  # noqa: B010

    db = FaissDB(config)
    query_service = Query(config, db)

    results = query_service.query(args.query)

    print(f"\nQuery: {args.query!r}")
    print(f"Results ({len(results)}):\n")
    for i, text in enumerate(results, start=1):
        preview = text.replace("\n", " ").strip()
        print(f"{i}. {preview}\n")


if __name__ == "__main__":
    main()
