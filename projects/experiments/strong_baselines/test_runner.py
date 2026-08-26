#!/usr/bin/env python3
from pathlib import Path
import json,shutil,subprocess,sys
root=Path(__file__).resolve().parent;temp=root/".test_output"
if temp.exists():shutil.rmtree(temp)
temp.mkdir();data=temp/"data";data.mkdir();(data/"arch.xml").write_text("<architecture/>");(data/"design.blif").write_text(".model x\n.end\n")
sdc=data/"design.sdc";sdc.write_text("create_clock -period 10 clk\n")
cases=temp/"cases.json";cases.write_text(json.dumps({"cases":[{"id":"tiny","architecture":"data/arch.xml","circuit":"data/design.blif","sdc":"data/design.sdc","route_chan_width":20,"max_router_iterations":400}]}))
environment=dict(__import__("os").environ);environment["VPR_BIN"]=sys.executable
subprocess.run([sys.executable,str(root/"run_strong_baselines.py"),"--baseline","vpr_serial","--cases",str(cases),"--output",str(temp/"runs"),"--dry-run"],check=True,env=environment)
record=json.loads((temp/"runs/vpr_serial/tiny/run.json").read_text())
if record["status"]!="dry_run" or len(record["inputs"])!=3:raise SystemExit("baseline audit record failed")
if "--route" in record["command"] or not Path(record["command"][record["command"].index("--route_file")+1]).is_absolute():raise SystemExit("baseline VPR flow/path construction failed")
if "--sdc_file" not in record["command"] or "--max_router_iterations" not in record["command"]:raise SystemExit("baseline VPR case options failed")
sample=temp/"vpr.log";sample.write_text("Circuit successfully routed with a channel width factor of 200.\nTotal wirelength: 123\nFinal critical path delay: 4.5 ns\n")
result=subprocess.run([sys.executable,str(root/"parse_qor.py"),str(sample)],check=True,text=True,stdout=subprocess.PIPE)
metrics=json.loads(result.stdout)
if metrics["vpr_wirelength"]!=123 or metrics["vpr_cpd_ns"]!=4.5 or not metrics["vpr_routed"]:raise SystemExit("QoR parser failed")
shutil.rmtree(temp);print("strong_baseline_tests: PASS")
