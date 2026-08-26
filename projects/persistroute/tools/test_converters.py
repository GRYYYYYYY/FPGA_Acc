#!/usr/bin/env python3
from pathlib import Path
import csv, json, shutil, struct, subprocess, sys

root=Path(__file__).resolve().parent
temp=root/".test_output"
if temp.exists(): shutil.rmtree(temp)
temp.mkdir();binary=temp/"graph.bin";placement=temp/"place.csv"
subprocess.run([sys.executable,str(root/"vpr_rr_graph_convert.py"),str(root/"fixtures/tiny_rr_graph.xml"),str(binary)],check=True)
subprocess.run([sys.executable,str(root/"vpr_rr_graph_convert.py"),str(binary),"--validate-only"],check=True)
subprocess.run([sys.executable,str(root/"vpr_place_convert.py"),str(root/"fixtures/tiny.place"),str(placement)],check=True)
with placement.open(encoding="utf-8") as stream: rows=list(csv.DictReader(stream))
if len(rows)!=2 or rows[0]["block"]!="src" or rows[1]["x"]!="1": raise SystemExit("placement conversion failed")
connections=temp/"connections.csv"
subprocess.run([sys.executable,str(root/"vpr_route_connections.py"),str(root/"fixtures/tiny.route"),str(connections)],check=True)
with connections.open(encoding="utf-8") as stream: connection_rows=list(csv.DictReader(stream))
if len(connection_rows)!=2 or connection_rows[1]["source"]!="0" or connection_rows[1]["sink"]!="3": raise SystemExit("VPR route connection extraction failed")
prefix=temp/"xrt_input"
subprocess.run([sys.executable,str(root/"pack_hls_inputs.py"),str(root/"fixtures/tiny_rr_graph.xml"),
                str(root/"fixtures/tiny_connections.csv"),str(prefix)],check=True)
manifest=json.loads(Path(str(prefix)+".manifest.json").read_text(encoding="utf-8"))
expected={"nodes":(3,8),"edges":(2,8),"resources":(3,16),"tasks":(1,32)}
for name,(count,size) in expected.items():
    item=manifest["files"][name]
    if item["count"]!=count or item["record_bytes"]!=size or item["bytes"]!=count*size:
        raise SystemExit(f"bad packed {name} metadata")
task=struct.Struct("<IIIIHHIII").unpack(prefix.with_suffix(".tasks").read_bytes())
if task!=(7,12,0,2,32768,16,10,0,0): raise SystemExit("task ABI packing failed")
rw_prefix=temp/"rw_input"
subprocess.run([sys.executable,str(root/"rapidwright_csv_to_hls.py"),str(root/"fixtures/rw_export"),str(rw_prefix)],check=True)
rw_manifest=json.loads(Path(str(rw_prefix)+".manifest.json").read_text(encoding="utf-8"))
if rw_manifest["files"]["edges"]["count"]!=3: raise SystemExit("bidirectional PIP expansion failed")
route_csv=temp/"routes.csv"
subprocess.run([sys.executable,str(root/"paths_to_rapidwright.py"),str(root/"fixtures/rw_export"),str(rw_prefix)+".edge_catalog.csv",str(root/"fixtures/rw_paths.csv"),str(route_csv)],check=True)
with route_csv.open(encoding="utf-8") as stream: route_rows=list(csv.DictReader(stream))
if len(route_rows)!=2 or route_rows[1]["end_wire"]!="SINK": raise SystemExit("RapidWright path inversion failed")
shutil.rmtree(temp)
print("converter_tests: PASS")
