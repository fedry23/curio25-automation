"""Find the oldest complete candidate batch without an archived research report.

This module selects an existing draft. It never invents facts, approves
sources, downloads media, or publishes a video.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
import re
from pathlib import Path

DATE_FILE=re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")


def pending_batches(root):
    directory=Path(root)/"data/candidates"
    batches=[]
    if not directory.is_dir():
        return batches
    for source in sorted(directory.iterdir()):
        match=DATE_FILE.fullmatch(source.name)
        if not match or not source.is_file():
            continue
        stamp=match.group(1)
        date.fromisoformat(stamp)
        if (directory/f"research-{stamp}"/"source_report.json").is_file():
            continue
        doc=json.loads(source.read_text(encoding="utf-8"))
        facts=doc.get("facts")
        if not isinstance(facts,list) or len(facts)!=25:
            raise ValueError(f"Lote de candidatos incompleto: {source.name}")
        identifiers=[f.get("id") for f in facts]
        if not all(isinstance(k,str) and k for k in identifiers) or len(set(identifiers))!=25:
            raise ValueError(f"IDs de datos duplicados o inválidos: {source.name}")
        batches.append(stamp)
    return batches


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    args=parser.parse_args()
    batches=pending_batches(args.root)
    print(batches[0] if batches else "NONE")


if __name__=="__main__":
    main()
