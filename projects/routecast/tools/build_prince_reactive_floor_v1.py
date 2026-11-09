"""Same-binary identity, full replacement, and non-suppressing reactive-floor modes."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_reactive_floor_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_final_other_oracle_v1_2026-10-20';p=json.loads((old/'protocol.json').read_text());s=(old/'observer.cpp').read_text();needle=' float marginal_excess=float(owned)+future_other;';assert s.count(needle)==1;s=s.replace(needle,needle+'\n if(std::getenv("ROUTECAST_REACTIVE_FLOOR")&&!std::getenv("ROUTECAST_LABEL_OTHER_ORACLE"))throw std::runtime_error("floor requires oracle mode");\n if(inject&&std::getenv("ROUTECAST_REACTIVE_FLOOR"))marginal_excess=std::max(float(occupancy),marginal_excess);');needle=' if(!inject&&qbits(replacement)!=qbits(original))';assert needle in s;s=s.replace(needle,' if(inject&&std::getenv("ROUTECAST_REACTIVE_FLOOR")&&replacement<original)throw std::runtime_error("reactive floor lowered native cost");\n'+needle)
 op=D/'observer.cpp';op.write_text(s);compile=p['compile'].copy();compile[compile.index('-c')+1]=str(op);compile[compile.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(old/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');paths=[Path(__file__),old/'protocol.json',old/'receipt.json',old/'observer.cpp',op,R/'experiments/prince_final_other_oracle_trial_v1_2026-10-20/reactive_floor_ablation_design_v1.json',*[Path(x) for x in link if not x.startswith('-') and Path(x).is_file() and x!=str(D/'observer.o')]];bindings={str(x):sha(x) for x in paths};(D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Component ablation only: after same ready event full replacement H=I+labelF versus floor H=max(liveO,I+labelF). Same identity and full-replacement paths preserved. Numeric original-cost lower bound asserted on every floor return. Labels not deployable forecast.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',op,D/'observer.o']}),indent=2)+'\n')
if __name__=='__main__':main()
