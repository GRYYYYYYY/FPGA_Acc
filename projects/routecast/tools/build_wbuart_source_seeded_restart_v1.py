"""Private opt-in whole-NET seeded restart on corrected native routing closure."""
import json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R/'build/native_excess_preload_state_v2_2026-10-19';BASE=R/'build/wbuart_corrected_utility_native_v1_2026-10-20';D=R/'build/wbuart_source_seeded_restart_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);(D/'source').mkdir();proof=json.loads((BASE/'receipt.json').read_text());assert sha(proof['binary'])==proof['binary_sha256'];assert all(sha(p)==h for p,h in proof['bindings'].items());old=json.loads((OLD/'protocol.json').read_text());src=OLD/'source/route.cpp';s=src.read_text();needle='    CBRR connections_inf{net_list, route_ctx.net_rr_terminals, is_flat};';assert s.count(needle)==1
 insert='''    const char* source_restart_flag=std::getenv("ROUTECAST_SOURCE_SEEDED_RESTART");
    const bool source_restart=source_restart_flag && std::string(source_restart_flag)=="1";
    if(source_restart) {
        if(!routecast_seed || !*routecast_seed || retained_input || is_flat ||
           !router_opts.with_timing_analysis || router_opts.initial_timing!=e_router_initial_timing::LOOKAHEAD ||
           std::getenv("ROUTECAST_PRESERVE_PARTIAL_FIRST_ITERATION"))
            throw std::runtime_error("source-seeded restart requires explicit file seed and clustered timing LOOKAHEAD without other retention mode");
        routecast_firstpass_partial.assign(route_ctx.route_trees.size(),0);
        size_t retained=0,missing=0,pins=0;
        for(auto net:net_list.nets()) {
            if(net_list.net_is_ignored(net))continue;
            const auto& tree=route_ctx.route_trees[net];
            if(tree) {
                if(tree->root().inode!=route_ctx.net_rr_terminals[net][0])throw std::runtime_error("restart SOURCE mismatch");
                for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                    auto sink=tree->find_by_isink(pin);
                    if(!sink || sink->inode!=route_ctx.net_rr_terminals[net][pin])throw std::runtime_error("restart requires complete retained NET");
                    net_delay[net][pin]=sink->Tdel;++pins;
                }
                routecast_firstpass_partial[size_t(net)]=1;++retained;
            } else {
                ++missing;
                for(size_t pin=1;pin<net_list.net_pins(net).size();++pin)net_delay[net][pin]=1.e-9f;
            }
        }
        if(!feasible_routing())throw std::runtime_error("restart seed occupancy infeasible");
        VTR_LOG("ROUTECAST_SOURCE_RESTART retained=%zu missing=%zu retained_pins=%zu missing_delay=1e-9\\n",retained,missing,pins);
        for(auto net:net_list.nets())if(!net_list.net_is_ignored(net))for(size_t pin=1;pin<net_list.net_pins(net).size();++pin)
            VTR_LOG("ROUTECAST_SOURCE_RESTART_DELAY net=%zu pin=%zu value=%a\\n",size_t(net),pin,double(net_delay[net][pin]));
        timing_info->update();
    }
'''
 s=s.replace(needle,insert+needle);condition='if (router_opts.with_timing_analysis && router_opts.initial_timing == e_router_initial_timing::LOOKAHEAD)';assert s.count(condition)==1;s=s.replace(condition,'if (!source_restart && router_opts.with_timing_analysis && router_opts.initial_timing == e_router_initial_timing::LOOKAHEAD)');assert s.replace(insert,'').replace('if (!source_restart && router_opts.with_timing_analysis','if (router_opts.with_timing_analysis')==src.read_text()
 source=D/'source/route.cpp';source.write_text(s)
 for h in (OLD/'source').glob('*.h'):shutil.copyfile(h,D/'source'/h.name)
 compile=old['compile'].copy();compile[compile.index('-c')+1]=str(source);compile[compile.index('-o')+1]=str(D/'route.o');link=json.loads((BASE/'protocol.json').read_text())['link'];link=[str(D/'route.o') if x==str(OLD/'route.o') else str(D/'sequence_vpr') if x==str(BASE/'sequence_vpr') else x for x in link];assert str(D/'route.o') in link and any(x.endswith('group_or.o') for x in link)
 bindings={str(p):sha(p) for p in [Path(__file__),BASE/'receipt.json',BASE/'protocol.json',src,source,*list((D/'source').glob('*.h'))]}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps({'compile':compile,'link':link,'bindings':bindings,'scope':'Opt-in complete retained NET first-pass preservation and tree delays/missing1ns initialization; existing loader strict placement verification retained. Disabled parity and native qualification pending. Not full native state continuation.'},indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps({'binary':str(D/'sequence_vpr'),'binary_sha256':sha(D/'sequence_vpr'),'bindings':{**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},'native_qualification_pending':True},indent=2)+'\n');print('SOURCE_SEEDED_RESTART_PRIVATE_BUILD_PASS')
if __name__=='__main__':main()
