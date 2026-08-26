#!/usr/bin/env python3
"""Extract connection endpoints from an official VPR text .route file.

VPR route trees can branch and repeat trunk nodes. PersistRoute only needs the
net SOURCE and each terminal SINK to create connection-level tasks; the exact
existing route tree remains in the .route file for baseline/QoR comparison.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path

NET=re.compile(r"^\s*Net\s+(\d+)\s+\((.*)\)\s*$")
NODE=re.compile(r"^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b")

def convert(source:Path,output:Path,criticality:int,max_hops:int):
    tasks=[];net_id=None;net_name=None;source_node=None
    for line_no,line in enumerate(source.read_text(encoding="utf-8",errors="replace").splitlines(),1):
        net_match=NET.match(line)
        if net_match:
            net_id=int(net_match.group(1));net_name=net_match.group(2);source_node=None;continue
        node_match=NODE.match(line)
        if not node_match or net_id is None:continue
        node_id,node_type=int(node_match.group(1)),node_match.group(2)
        if node_type=="SOURCE":
            if source_node is None:source_node=node_id
            elif source_node!=node_id:raise ValueError(f"net {net_id} has inconsistent SOURCE at line {line_no}")
        elif node_type=="SINK":
            if source_node is None:raise ValueError(f"net {net_id} SINK before SOURCE at line {line_no}")
            tasks.append((len(tasks),net_id,net_name,source_node,node_id,criticality,max_hops,len(tasks),0))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8",newline="") as f:
        out=csv.writer(f);out.writerow(["id","net_id","net","source","sink","criticality_q","max_hops","priority","epoch"]);out.writerows(tasks)
    return {"source":str(source.resolve()),"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"connections":len(tasks),"output_sha256":hashlib.sha256(output.read_bytes()).hexdigest()}

def main():
    p=argparse.ArgumentParser();p.add_argument("input",type=Path);p.add_argument("output",type=Path);p.add_argument("--criticality-q",type=int,default=0);p.add_argument("--max-hops",type=int,default=65535);a=p.parse_args()
    if not 0<=a.criticality_q<=65535 or not 1<=a.max_hops<=65535:p.error("quantized fields must fit uint16")
    print(json.dumps(convert(a.input,a.output,a.criticality_q,a.max_hops),indent=2))
if __name__=="__main__":main()
