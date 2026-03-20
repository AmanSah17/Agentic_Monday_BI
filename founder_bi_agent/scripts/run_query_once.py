from __future__ import annotations

import json
import sys

from founder_bi_agent.backend.service import run_founder_query


def main() -> None:
    question = (
        "How is our pipeline by sector this quarter?"
        if len(sys.argv) < 2
        else " ".join(sys.argv[1:])
    )
    result = run_founder_query(question)
    print(json.dumps(result, ensure_ascii=True, default=str, indent=2))


if __name__ == "__main__":
    main()
