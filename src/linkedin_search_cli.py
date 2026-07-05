from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .linkedin_agent import search_linkedin_posts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-posts", type=int, default=8)
    args = parser.parse_args()

    queries = json.loads(Path(args.queries).read_text(encoding="utf-8"))
    results = search_linkedin_posts(queries, max_posts_per_query=args.max_posts)
    print(f"Matched {len(results)} opportunity email(s).", flush=True)
    Path(args.output).write_text(
        json.dumps([asdict(result) for result in results], indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
