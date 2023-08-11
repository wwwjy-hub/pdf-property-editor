#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from pdfrw import PdfReader, PdfWriter

PROPERTY_KEYWORDS = "/Keywords"
STRATEGY_MERGE = "merge"
STRATEGY_OVERWRITE = "overwrite"
STRATEGIES = [STRATEGY_OVERWRITE, STRATEGY_MERGE]

USER_KEYS = [
    "Ab",
    "A",
    "Bb",
    "B",
    "C",
    "C#",
    "Db",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "G#",
]

ENHARMONICS = {
    "Ab": "G#/Ab",
    "G#": "G#/Ab",
    "A#": "A#/Bb",
    "Bb": "A#/Bb",
    "C#": "C#/Db",
    "Db": "C#/Db",
    "D#": "D#/Eb",
    "Eb": "D#/Eb",
}


def parseargs() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(title="actions", required=True, dest="action")

    read = sp.add_parser("read", help="read pdf properties")
    read.add_argument("file", help="PDF file")

    write = sp.add_parser("write", help="writer properties")
    write.add_argument("file", help="PDF file")

    write.add_argument(
        "--key",
        help="write the song key",
        choices=USER_KEYS,
    )
    write.add_argument("--chords", action="store_true")
    write.add_argument("--jon", action="store_true")
    write.add_argument(
        "--instrument", "-i", choices=["bass", "guitar", "ukulele"], nargs="+"
    )
    write.add_argument("--tab", "-t", action="store_true")
    write.add_argument("--youtube", "--yt", help="youtube link")
    write.add_argument("--spotify", "--sp", help="spotify link")
    strategy = write.add_mutually_exclusive_group(required=True)
    strategy.add_argument(
        "--merge", action="store_true", help="merge keywords instead of overwriting"
    )
    strategy.add_argument("--overwrite", action="store_true", help="overwrite keywords")
    args = p.parse_args()

    if not args.file.lower().endswith(".pdf"):
        sys.exit(f"{sys.argv[0]} only works with PDF files")

    args.file = Path(args.file)
    if not args.file.exists():
        sys.exit(f"Not a file: {args.file}")

    if args.merge:
        args.__dict__["strategy"] = STRATEGY_MERGE
    elif args.overwrite:
        args.__dict__["strategy"] = STRATEGY_OVERWRITE

    if args.key:
        args.key = ENHARMONICS.get(args.key, args.key)
    return args


def gather_properties(args: argparse.Namespace) -> dict:
    keywords = []
    if args.chords:
        keywords.append("#chords")
    if args.jon:
        keywords.append("#jon")
    if args.key:
        keywords.append(f"#key={args.key}")
    if args.youtube:
        keywords.append(args.youtube)
    if args.spotify:
        keywords.append(args.spotify)
    if args.instrument:
        for i in args.instrument:
            keywords.append(f"#{i}")
    if args.tab:
        keywords.append("#tab")

    props = {}
    if keywords:
        props[PROPERTY_KEYWORDS] = "; ".join(keywords)
    return props


def read_properties(file: str) -> dict:
    """
    Return a dict of properties

    Args:
        file (str): filename

    Returns:
        dict: properties
    """
    print(f"reading properties for {file}")
    props = {}
    with open(file, "rb") as fh:
        reader = PdfReader(fh)
        if reader.Info:
            for n, v in reader.Info.items():  # type:ignore
                props[n] = v
    return props


def write_properties(file: str, properties: dict, strategy: str):
    """
    Write properties to the PDF

    Args:
        file (str): Filename
        properties (dict): Dictionary of properties to write. Keys must be standard PDF property keys
        strategy (str): one of STRATEGIES
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"invalid stategy: {strategy}")
    print(f"Writing properties to {file}: {properties=}")
    is_modified = False
    with open(file, "rb") as fh:
        writer = PdfReader(fh)
        if not writer.Info:
            writer.Info = {}
        if PROPERTY_KEYWORDS in properties:
            kw = properties.get(PROPERTY_KEYWORDS, "")
            if strategy == STRATEGY_MERGE:
                writer.Info.Keywords += f"; {kw}"  # type:ignore
            elif strategy == STRATEGY_OVERWRITE:
                writer.Info.Keywords = kw  # type:ignore
            is_modified = True
        if is_modified:
            print(f"Saving {file}")
            PdfWriter(file, trailer=writer).write()
    read_properties(file)
    print("")


def print_props(file: str, props: dict):
    print(f"Properties for {file}")
    for n, v in props.items():
        print(f"{n:13s}: {v}")


if __name__ == "__main__":
    args = parseargs()

    if args.action == "read":
        props = read_properties(args.file)
        print_props(args.file, props)
        sys.exit(0)

    if args.action == "write":
        props = gather_properties(args)
        write_properties(args.file, props, args.strategy)
        new_props = read_properties(args.file)
        print_props(args.file, new_props)
