from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.schemas import ReplicationRequest
from app.services.replication_service import analyse_external_replication


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse a standard external forecast replication ledger.")
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--candidate", default="candidate")
    parser.add_argument("--comparator", default="comparator")
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--block-size", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyse_external_replication(
        args.ledger.read_bytes(),
        ReplicationRequest(
            candidate_name=args.candidate,
            comparator_name=args.comparator,
            bootstrap_samples=args.bootstrap_samples,
            block_size=args.block_size,
            seed=args.seed,
        ),
    )
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
