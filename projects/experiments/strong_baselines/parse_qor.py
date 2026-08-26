#!/usr/bin/env python3
"""Conservative QoR extraction. Missing metrics remain null, never zero."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

PATTERNS={
 "vpr_cpd_ns":[r"Final critical path delay.*?([0-9.]+)\s*ns",r"critical path delay.*?([0-9.]+)\s*ns"],
 "vpr_wirelength":[r"Total wirelength:\s*([0-9]+)"],
 "vpr_routed":[r"Circuit(?: is)? successfully routed",r"Successfully routed after\s+[0-9]+\s+routing iterations"],
 "wns_ns":[r"WNS\(ns\).*?\n\s*(-?[0-9.]+)",r"Slack \(VIOLATED\).*?(-?[0-9.]+)ns"],
 "tns_ns":[r"TNS\(ns\).*?\n\s*-?[0-9.]+\s+(-?[0-9.]+)"],
 "unrouted_nets":[r"# of unrouted nets\s*[:|]\s*([0-9]+)"],
}
def parse(text):
 out={key:None for key in PATTERNS}
 for key,patterns in PATTERNS.items():
  for pattern in patterns:
   match=re.search(pattern,text,re.I|re.S)
   if match: out[key]=True if key=="vpr_routed" else float(match.group(1));break
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument("inputs",type=Path,nargs="+");p.add_argument("--output",type=Path);a=p.parse_args();text="\n".join(x.read_text(encoding="utf-8",errors="replace") for x in a.inputs);out=parse(text);encoded=json.dumps(out,indent=2,sort_keys=True);print(encoded)
 if a.output:a.output.write_text(encoded+"\n",encoding="utf-8")
if __name__=="__main__":main()
