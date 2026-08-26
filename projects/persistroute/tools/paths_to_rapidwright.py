#!/usr/bin/env python3
"""Convert PersistRoute node paths back to RapidWright PIP route CSV."""
from __future__ import annotations
import argparse,csv
from pathlib import Path

def convert(export_dir:Path,edge_catalog:Path,paths:Path,output:Path):
    connections={}
    with (export_dir/"connections.csv").open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f): connections[int(row["id"])]=(row["net"],int(row["source"]))
    edges={}
    with edge_catalog.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f): edges.setdefault((int(row["src"]),int(row["dst"])),[]).append(row)
    task_paths={}
    with paths.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f): task_paths.setdefault(int(row["task_id"]),[]).append((int(row["path_index"]),int(row["resource_id"])))
    output.parent.mkdir(parents=True,exist_ok=True);count=0
    with output.open("w",encoding="utf-8",newline="") as f:
        out=csv.writer(f);out.writerow(["net","tile","start_wire","end_wire","reversed"])
        for task_id in sorted(task_paths):
            if task_id not in connections: raise ValueError(f"unknown task {task_id}")
            net,current=connections[task_id]
            ordered=sorted(task_paths[task_id])
            if [i for i,_ in ordered]!=list(range(len(ordered))): raise ValueError(f"non-contiguous path indices for task {task_id}")
            for _,nxt in ordered:
                choices=edges.get((current,nxt),[])
                if len(choices)!=1: raise ValueError(f"edge {current}->{nxt} has {len(choices)} PIP mappings")
                edge=choices[0];out.writerow([net,edge["tile"],edge["start_wire"],edge["end_wire"],edge["reversed"]]);current=nxt;count+=1
    return count

def main():
    p=argparse.ArgumentParser();p.add_argument("export_dir",type=Path);p.add_argument("edge_catalog",type=Path);p.add_argument("paths",type=Path);p.add_argument("output",type=Path);a=p.parse_args();print(f"routes={convert(a.export_dir,a.edge_catalog,a.paths,a.output)}")
if __name__=="__main__":main()
