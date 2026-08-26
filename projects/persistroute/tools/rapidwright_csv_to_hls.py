#!/usr/bin/env python3
"""Pack RapidWrightBridge CSV export into PersistRoute/XRT arrays."""
from __future__ import annotations
import argparse, csv, hashlib, json, struct
from pathlib import Path

NODE=struct.Struct("<IHH"); EDGE=struct.Struct("<IHH"); RESOURCE=struct.Struct("<HHHHII"); TASK=struct.Struct("<IIIIHHIII")

def write_array(path, rows, record):
    with path.open("wb") as out:
        for row in rows: out.write(record.pack(*row))
    return {"path":path.name,"count":len(rows),"record_bytes":record.size,"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

def pack(export_dir:Path,prefix:Path,base_cost:int,delay_q:int):
    with (export_dir/"nodes.csv").open(encoding="utf-8-sig",newline="") as f: source_nodes=list(csv.DictReader(f))
    source_nodes.sort(key=lambda r:int(r["id"]));ids=[int(r["id"]) for r in source_nodes]
    if ids!=list(range(len(ids))): raise ValueError("RapidWright node IDs must be dense")
    grouped=[[] for _ in source_nodes];catalog=[]
    with (export_dir/"pips.csv").open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            src,dst=int(row["src"]),int(row["dst"])
            if src>=len(grouped) or dst>=len(grouped): raise ValueError("PIP outside node range")
            grouped[src].append((dst,base_cost,delay_q));catalog.append((src,dst,row["tile"],row["start_wire"],row["end_wire"],"false"))
            if row["bidirectional"].lower()=="true":
                grouped[dst].append((src,base_cost,delay_q));catalog.append((dst,src,row["tile"],row["start_wire"],row["end_wire"],"true"))
    nodes=[];edges=[];cursor=0
    for outgoing in grouped:
        unique=sorted(set(outgoing));nodes.append((cursor,len(unique),0));edges.extend(unique);cursor+=len(unique)
    resources=[(0,1,256,0,0,0xffffffff) for _ in nodes]
    tasks=[]
    with (export_dir/"connections.csv").open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f): tasks.append(tuple(int(row[k],0) for k in ("id","net_id","source","sink","criticality_q","max_hops","priority","epoch"))+(0,))
    tasks.sort(key=lambda r:(r[6],r[0]));prefix.parent.mkdir(parents=True,exist_ok=True)
    files={"nodes":write_array(prefix.with_suffix(".nodes"),nodes,NODE),"edges":write_array(prefix.with_suffix(".edges"),edges,EDGE),"resources":write_array(prefix.with_suffix(".resources"),resources,RESOURCE),"tasks":write_array(prefix.with_suffix(".tasks"),tasks,TASK)}
    catalog_path=Path(str(prefix)+".edge_catalog.csv")
    with catalog_path.open("w",encoding="utf-8",newline="") as f:
        out=csv.writer(f);out.writerow(["src","dst","tile","start_wire","end_wire","reversed"]);out.writerows(sorted(catalog,key=lambda r:(r[0],r[1],r[2],r[3],r[4],r[5])))
    manifest={"schema":"PERSISTROUTE_RW_XRT_INPUT_V1","export_dir":str(export_dir.resolve()),"base_cost_q":base_cost,"delay_q":delay_q,"files":files,"edge_catalog":{"path":catalog_path.name,"count":len(catalog),"sha256":hashlib.sha256(catalog_path.read_bytes()).hexdigest()}}
    Path(str(prefix)+".manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser();p.add_argument("export_dir",type=Path);p.add_argument("output_prefix",type=Path);p.add_argument("--base-cost-q",type=int,default=256);p.add_argument("--delay-q",type=int,default=1);a=p.parse_args();print(json.dumps(pack(a.export_dir,a.output_prefix,a.base_cost_q,a.delay_q),indent=2))
if __name__=="__main__":main()
