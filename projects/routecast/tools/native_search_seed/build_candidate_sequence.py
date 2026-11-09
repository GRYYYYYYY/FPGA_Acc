import json,subprocess,shutil
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
root=Path.cwd();base=root/'build/native_candidate_move_accept_scoped_2026-10-06';out=root/'build/native_candidate_sequence_2026-10-06';out.mkdir();src=out/'source';src.mkdir();p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());shared={f:sha(f) for f in p['inputs_sha256']}
s=(base/'source/route.cpp').read_text();start='    if (std::getenv("ROUTECAST_TIMING_RESTORE_PROBE")) {'
s=s.replace(start,start+'''\n        const char* raw_sequence=std::getenv("ROUTECAST_MOVE_SEQUENCE");
        std::string sequence=raw_sequence?raw_sequence:"A";
        if(sequence.empty() || sequence.find_first_not_of("AR")!=std::string::npos)throw std::runtime_error("invalid move sequence");
        for(size_t step=0;step<sequence.size();++step) {
        VTR_LOG("ROUTECAST sequence step=%zu decision=%c\\n",step,sequence[step]);
''',1)
s=s.replace('std::string original_seed=std::getenv("ROUTECAST_NATIVE_SEED");','const char* saved_seed_env=std::getenv("ROUTECAST_NATIVE_SEED");\n        std::string original_seed=saved_seed_env?saved_seed_env:"";')
s=s.replace('if(std::getenv("ROUTECAST_ACCEPT_CANDIDATE")) {',"if(sequence[step]=='A') {")
s=s.replace('                return true;','''                if(step+1==sequence.size())return true;
                sync_netlists_to_routing(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement(),quiet);
                continue;''',1)
s=s.replace('FILE* candidate_file=std::fopen("candidate.route","w");','std::string candidate_name="candidate_"+std::to_string(step)+".route";\n            FILE* candidate_file=std::fopen(candidate_name.c_str(),"w");')
needle='        VTR_LOG("ROUTECAST restored delay matrix and all edge-delay/STA metric observations\\n");\n    }'
assert s.count(needle)==1
s=s.replace(needle,'''        VTR_LOG("ROUTECAST restored delay matrix and all edge-delay/STA metric observations\\n");
        if(step+1==sequence.size()) {
            routecast_arm_sync_ticket(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement());
            return true;
        }
        }
    }''')
(src/'route.cpp').write_text(s);shutil.copyfile(base/'source/sync_once.cpp',src/'sync_once.cpp');shutil.copyfile(__file__,src/'build.py')
obj=out/'route.o';cmd=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(obj)]
with (out/'compile.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
import re
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(root/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(obj),str(base/'sync_once.o'),wrap]
with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(f)==h for f,h in shared.items())
(out/'receipt.json').write_text(json.dumps({'shared_inputs_sha256':shared,'binary_sha256':sha(out/'sequence_vpr'),'source_sha256':{str(f):sha(f) for f in src.iterdir()},'scope':'Serial same-process recursive cold-candidate sequence, fixed compatible block pair. Not a production transaction.'},indent=2)+'\n');print('built')
