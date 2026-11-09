"""Private exporter TU, existing VPR archives readonly; native slack not crit inversion."""
import pathlib,json,subprocess,hashlib
R=pathlib.Path(__file__).resolve().parents[1];O=R/'build/native_prior_setup_slack_export_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);base=R/'build/timing_export_v7_2026-10-04/protocol.json';plan=json.loads(base.read_text());src=O/'source';src.mkdir();mainp=src/'main.cpp';mainp.write_text((R/'tools/native_timing/main.cpp').read_text());h=(R/'tools/native_timing/routecast_export.h').read_text();helper='''
#include <cmath>
#include <limits>
#include <sstream>
#include <cstring>
#include <cstdint>
static uint32_t routecast_float_bits(float x){static_assert(sizeof(float)==4,"float32 required");uint32_t b;std::memcpy(&b,&x,4);return b;}
static std::string routecast_slack_text(float x){if(!std::isfinite(x))return "null";std::ostringstream out;out<<std::setprecision(std::numeric_limits<float>::max_digits10)<<x;return out.str();}
''';h=h.replace('#pragma once','#pragma once\n'+helper);lines=[]
 for line in h.splitlines():
  if 'timing->setup_pin_criticality(ap)<<' in line:line=line.replace('<<"}";', '<<",\\\"setup_slack_s\\\":"<<routecast_slack_text(timing->setup_pin_slack(ap))<<",\\\"setup_slack_float32_bits\\\":"<<routecast_float_bits(timing->setup_pin_slack(ap))<<"}";')
  lines.append(line)
  if 'calculate_clb_net_pin_criticality(*timing,lookup,ParentPinId(pin),false)' in line:
   lines.extend(['               <<",\\\"setup_slack_s\\\":"<<routecast_slack_text(calculate_clb_net_pin_setup_slack(*timing,lookup,pin))','               <<",\\\"setup_slack_float32_bits\\\":"<<routecast_float_bits(calculate_clb_net_pin_setup_slack(*timing,lookup,pin))','               <<",\\\"native_route_delay_float32_bits\\\":"<<routecast_float_bits(delay[ParentNetId(net)][clb.pin_net_index(pin)])','               <<",\\\"clock_sink\\\":"<<(clb.port_type(clb.pin_port(pin))==PortType::CLOCK?"true":"false")','               <<",\\\"ignored_net\\\":"<<(clb.net_is_ignored(net)?"true":"false")'])
 hp=src/'routecast_export.h';hp.write_text('\n'.join(lines)+'\n');compile=plan['compile'].copy();compile[compile.index('-c')+1]=str(mainp);compile[compile.index('-o')+1]=str(O/'main.o');compile.insert(1,'-I'+str(src));link=[str(O/'main.o') if x.endswith('/main.o') else str(O/'routecast_prior_slack_export') if x==plan['link'][plan['link'].index('-o')+1] else x for x in plan['link']];bindings={str(p):sha(p) for p in [base,mainp,hp,pathlib.Path(__file__).resolve()]}
 for p in plan['shared_libraries']:assert sha(pathlib.Path(p))==plan['shared_libraries'][p];bindings[p]=plan['shared_libraries'][p]
 (O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,compile=compile,link=link,scope='One private exporter translation unit, original shared archives unchanged. Export raw native setup slack and bits; not converting criticality to slack or admitting timing budgets.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  print('BUILD',name,flush=True)
  with (O/(name+'.log')).open('x') as out:subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,check=True)
 for p,h in bindings.items():assert sha(pathlib.Path(p))==h
 (O/'receipt.json').write_text(json.dumps(dict(status='PRIVATE_NATIVE_SETUP_SLACK_EXPORT_BUILT',bindings=bindings,binary=str(O/'routecast_prior_slack_export'),binary_sha256=sha(O/'routecast_prior_slack_export')),indent=2)+'\n');print('SLACK_EXPORT_BUILT',flush=True)
if __name__=='__main__':main()
