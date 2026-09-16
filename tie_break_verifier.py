#!/usr/bin/env python3
"""Read-only metadata regeneration; no scientific driver imports or execution.

The two functions below are copied from the original metadata-gate generator
extract_matr_primary_metadata.py (SHA-256 recorded in the receipt).
POLICIES contains only original protocol identities, no B assignments or labels.
Run: python3 tie_break_verifier.py > tie-break-receipt.json
The frozen manifest is opened read-only; regenerated CSV bytes remain in memory.
"""
import csv
import hashlib
import io
import json
import unicodedata
from pathlib import Path

FROZEN_SHA256 = "96695e534718733469ba108ee3c1372e29351710235d5b47020f6bd9ae2ce722"
ORIGINAL_GENERATOR_SHA256 = 'd8d2fa56596e608cc8eb45b0d631c84d7568917d61ef1aa571e0f46b9de70efd'
ORIGINAL_METADATA_SHA256 = 'd9332d95468d9c9a767f42363d9b09612f17f2af518de24e728ed05e2056c753'
POLICIES = ['1C(4%)-6C', '2C(10%)-6C', '2C(2%)-5C', '2C(7%)-5.5C', '3.6C(2%)-4.85C', '3.6C(22%)-5.5C', '3.6C(30%)-6C', '3.6C(80%)-3.6C', '3.6C(9%)-5C', '4.4C(24%)-5C', '4.4C(47%)-5.5C', '4.4C(55%)-6C', '4.4C(8%)-4.85C', '4.4C(80%)-4.4C', '4.65C(19%)-4.85C', '4.65C(44%)-5C', '4.65C(69%)-6C', '4.8C(80%)-4.8C', '4.9C(27%)-4.75C', '4.9C(61%)-4.5C', '4.9C(69%)-4.25C', '4C(13%)-5C', '4C(31%)-5', '4C(4%)-4.85C', '4C(40%)-6C', '4C(80%)-4C', '5.2C(10%)-4.75C', '5.2C(37%)-4.5C', '5.2C(50%)-4.25C', '5.2C(58%)-4C', '5.2C(66%)-3.5C', '5.2C(71%)-3C', '5.4C(40%)-3.6C', '5.4C(50%)-3C', '5.4C(60%)-3.6C', '5.4C(60%)-3C', '5.4C(70%)-3C', '5.4C(80%)-5.4C', '5.6C(25%)-4.5C', '5.6C(38%)-4.25C', '5.6C(47%)-4C', '5.6C(5%)-4.75C', '5.6C(58%)-3.5C', '5.6C(65%)-3C', '6C(20%)-4.5C', '6C(30%)-3.6C', '6C(31%)-4.25C', '6C(4%)-4.75C', '6C(40%)-3.6C', '6C(40%)-3C', '6C(40%)-4C', '6C(50%)-3.6C', '6C(50%)-3C', '6C(52%)-3.5C', '6C(60%)-3C', '7C(30%)-3.6C', '7C(40%)-3.6C', '7C(40%)-3C', '8C(15%)-3.6C', '8C(25%)-3.6C', '8C(35%)-3.6C']

def protocol_id(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip()

def minimum_change_split(
    rows_by_id: dict[str, dict[str, object]],
    train_ids: list[str],
    test_ids: list[str],
) -> tuple[list[str], list[str], int]:
    side = {cell: 0 for cell in train_ids} | {cell: 1 for cell in test_ids}
    grouped: dict[str, list[str]] = {}
    for cell in train_ids + test_ids:
        policy = protocol_id(str(rows_by_id[cell]["policy_readable"]))
        grouped.setdefault(policy, []).append(cell)

    groups = []
    for policy in sorted(grouped):
        cells = sorted(grouped[policy])
        train_count = sum(side[cell] == 0 for cell in cells)
        test_count = len(cells) - train_count
        groups.append((policy, cells, train_count, test_count))

    target = len(test_ids)
    # test-size -> (number of moved cells, lexicographic assignment bits)
    dp: dict[int, tuple[int, tuple[int, ...]]] = {0: (0, ())}
    for _, cells, train_count, test_count in groups:
        next_dp: dict[int, tuple[int, tuple[int, ...]]] = {}
        for count, (cost, bits) in dp.items():
            choices = (
                (0, test_count, 0),
                (1, train_count, len(cells)),
            )
            for bit, added_cost, added_test in choices:
                new_count = count + added_test
                candidate = (cost + added_cost, bits + (bit,))
                if new_count <= target and (
                    new_count not in next_dp or candidate < next_dp[new_count]
                ):
                    next_dp[new_count] = candidate
        dp = next_dp

    cost, bits = dp[target]
    train, test = [], []
    for bit, (_, cells, _, _) in zip(bits, groups):
        (test if bit else train).extend(cells)
    return sorted(train), sorted(test), cost

def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    root = Path(__file__).resolve().parent
    frozen = (root / "batteryml-protocol-generalization-split-manifest.csv").read_bytes()
    require(hashlib.sha256(frozen).hexdigest() == FROZEN_SHA256, "Frozen input hash mismatch")
    reader = csv.DictReader(io.StringIO(frozen.decode("utf-8"), newline=""))
    fields = reader.fieldnames
    rows = list(reader)
    policies = {hashlib.sha256(protocol_id(p).encode("utf-8")).hexdigest(): protocol_id(p)
                for p in POLICIES}
    require(len(policies) == len(POLICIES), "Duplicate protocol identity")
    regenerated, results = [], {}
    for universe, size in (("primary83", 83), ("sensitivity84", 84)):
        selected = [r for r in rows if r["universe"] == universe]
        require(len(selected) == size and len({r["cell_id"] for r in selected}) == size,
                "Universe membership mismatch")
        # Only A membership, A positions, cell IDs and protocol identity enter construction.
        metadata = {r["cell_id"]: {"policy_readable": policies[r["protocol_sha256"]]}
                    for r in selected}
        a = [[r["cell_id"] for r in sorted(selected, key=lambda r: int(r["a_position"]))
              if r["a_split"] == side] for side in ("train", "test")]
        require(list(map(len, a)) == [41, size - 41], "A counts mismatch")
        train, test, cost = minimum_change_split(metadata, *a)
        require(cost == 20, "Minimum cost mismatch")
        positions = {cell: (side, pos) for side, cells in (("train", train), ("test", test))
                     for pos, cell in enumerate(cells)}
        original_a = {cell: (side, pos) for side, cells in zip(("train", "test"), a)
                      for pos, cell in enumerate(cells)}
        for cell in sorted(metadata):
            a_side, a_pos = original_a[cell]
            b_side, b_pos = positions[cell]
            regenerated.append(dict(zip(fields, (universe, cell, a_side, a_pos, b_side, b_pos,
                hashlib.sha256(metadata[cell]["policy_readable"].encode("utf-8")).hexdigest(), cost))))
        expected = [[r["cell_id"] for r in sorted(selected, key=lambda r: int(r["b_position"]))
                     if r["b_split"] == side] for side in ("train", "test")]
        exact = [train, test] == expected
        results[universe] = {"exact_ordered_cell_match": exact, "minimum_total_moves": cost,
                             "train_count": len(train), "test_count": len(test)}
        require(exact, universe + " ordered-cell mismatch")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(regenerated)
    generated = output.getvalue().encode("utf-8")
    require(generated == frozen, "Regenerated manifest byte mismatch")
    print(json.dumps({
        "classification": "OBSERVED",
        "algorithm": "NFKC-strip policy string order; minimum moves; lexicographic bits train=0,test=1",
        "original_generator": "extract_matr_primary_metadata.py",
        "original_generator_sha256": ORIGINAL_GENERATOR_SHA256,
        "original_metadata": "primary_pool_84_metadata.csv",
        "original_metadata_sha256": ORIGINAL_METADATA_SHA256,
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "frozen_manifest_sha256": FROZEN_SHA256,
        "regenerated_manifest_sha256": hashlib.sha256(generated).hexdigest(),
        "manifest_byte_identical_match": True,
        "universes": results,
        "scientific_run_executed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
