#!/usr/bin/env python3
"""Auditable runner for VPR, RWRoute/CUFR and Vivado routing baselines."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def executable(name, env_name):
    configured=os.environ.get(env_name)
    found=shutil.which(configured or name)
    if not found: raise RuntimeError(f"{env_name} is unset and {name} is not on PATH")
    return found
def expand(path,base):
    value=Path(path)
    return (base/value).resolve() if not value.is_absolute() else value.resolve()

def command_for(profile,case,out):
    runner=profile["runner"]
    if runner=="literature_only": raise RuntimeError("B2 literature-only entries cannot be executed")
    if runner=="vpr":
        arch=expand(case["architecture"],case["_base"]);circuit=expand(case["circuit"],case["_base"])
        cmd=[executable("vpr","VPR_BIN"),str(arch),str(circuit),"--route_file",str(out/"design.route"),"--seed",str(case.get("seed",1)),"--num_workers",str(profile["workers"])]
        inputs=[arch,circuit]
        if "route_chan_width" in case: cmd += ["--route_chan_width",str(case["route_chan_width"])]
        if case.get("sdc"):
            sdc=expand(case["sdc"],case["_base"]);cmd += ["--sdc_file",str(sdc)];inputs.append(sdc)
        if case.get("read_rr_graph"):
            rr_graph=expand(case["read_rr_graph"],case["_base"]);cmd += ["--read_rr_graph",str(rr_graph)];inputs.append(rr_graph)
        option_flags={
            "max_router_iterations":"--max_router_iterations",
            "router_lookahead":"--router_lookahead",
            "initial_pres_fac":"--initial_pres_fac",
            "router_profiler_astar_fac":"--router_profiler_astar_fac",
        }
        for key,flag in option_flags.items():
            if key in case: cmd += [flag,str(case[key])]
        return cmd,inputs
    if runner=="rapidwright":
        source=expand(case["placed_dcp"],case["_base"]);target=out/"routed.dcp"
        return [executable("rapidwright","RAPIDWRIGHT_BIN"),profile["application"],str(source),str(target)], [source]
    if runner=="vivado":
        source=expand(case["placed_dcp"],case["_base"]);script=ROOT/"vivado_route.tcl"
        return [executable("vivado","VIVADO_BIN"),"-mode","batch","-source",str(script),"-tclargs",str(source),str(out)], [source,script]
    raise RuntimeError(f"unknown runner {runner}")

def version_command(profile,exe):
    if profile["runner"]=="vpr": return [exe,"--version"]
    if profile["runner"]=="vivado": return [exe,"-version"]
    if profile["runner"]=="rapidwright": return [exe,"--help"]
    return []

def main():
    p=argparse.ArgumentParser();p.add_argument("--baseline",required=True);p.add_argument("--cases",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--dry-run",action="store_true");p.add_argument("--timeout",type=int,default=86400);a=p.parse_args()
    registry=json.loads((ROOT/"baseline_registry.json").read_text(encoding="utf-8"));profile=registry["baselines"].get(a.baseline)
    if not profile: raise SystemExit(f"unknown baseline {a.baseline}")
    case_doc=json.loads(a.cases.read_text(encoding="utf-8"));base=a.cases.resolve().parent;results=[]
    for case_raw in case_doc["cases"]:
        case=dict(case_raw);case["_base"]=base;out=(a.output/a.baseline/case["id"]).resolve();out.mkdir(parents=True,exist_ok=True)
        try: cmd,inputs=command_for(profile,case,out)
        except RuntimeError as error:
            if a.dry_run: cmd=["<unavailable>",str(error)];inputs=[]
            else: raise
        record={"schema":"FPGA_ACC_RUN_V1","baseline":a.baseline,"evidence":profile["evidence"],"case":case["id"],"command":cmd,"cwd":str(out.resolve()),"inputs":[{"path":str(x),"sha256":digest(x)} for x in inputs if x.exists()],"host":{"platform":platform.platform(),"python":sys.version},"status":"dry_run" if a.dry_run else "running"}
        (out/"run.json").write_text(json.dumps(record,indent=2,sort_keys=True),encoding="utf-8")
        if a.dry_run: results.append(record);continue
        version=subprocess.run(version_command(profile,cmd[0]),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        (out/"version.log").write_text(version.stdout,encoding="utf-8",errors="replace")
        begin=time.perf_counter();run=subprocess.run(cmd,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=a.timeout);wall=time.perf_counter()-begin
        (out/"stdout.log").write_text(run.stdout,encoding="utf-8",errors="replace");(out/"stderr.log").write_text(run.stderr,encoding="utf-8",errors="replace")
        record.update({"status":"pass" if run.returncode==0 else "fail","returncode":run.returncode,"wall_s":wall,"tool_version_sha256":digest(out/"version.log")})
        (out/"run.json").write_text(json.dumps(record,indent=2,sort_keys=True),encoding="utf-8");results.append(record)
    print(json.dumps(results,indent=2));return 0 if all(x["status"] in ("pass","dry_run") for x in results) else 3
if __name__=="__main__":raise SystemExit(main())
