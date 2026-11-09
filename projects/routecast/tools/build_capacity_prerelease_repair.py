"""Private complete repair-cohort release after seed STA, before native search."""
import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'build/native_search_seed_v3_2026-10-06';dirty=root/'build/capacity_dirty_repair_2026-10-06';out=root/'build/capacity_prerelease_repair_2026-10-06';out.mkdir();p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());source=(base/'source/route.cpp').read_text();needle='    std::unique_ptr<NetPinTimingInvalidator> pin_timing_invalidator;';assert source.count(needle)==1;source=source.replace(needle,'''    const char* release_path=std::getenv("ROUTECAST_PRERELEASE_NET_NAMES");
    if(release_path) {
        if(!routecast_seed || !*routecast_seed || is_flat) throw std::runtime_error("prerelease requires cluster seed");
        std::ifstream file(release_path);if(!file)throw std::runtime_error("prerelease list open failed");
        std::unordered_set<std::string> names;std::string name;
        while(std::getline(file,name))if(!name.empty())names.insert(name);
        std::vector<ParentNetId> targets;
        for(auto net:net_list.nets())if(names.erase(net_list.net_name(net))) {
            if(net_list.net_is_ignored(net)||route_ctx.net_status.is_fixed(net)||!route_ctx.route_trees[net])throw std::runtime_error("invalid release target");
            targets.push_back(net);
        }
        if(!names.empty())throw std::runtime_error("unknown release target");
        for(auto net:targets) {
            pathfinder_update_cost_from_route_tree(route_ctx.route_trees[net]->root(),-1);
            route_ctx.route_trees[net]=vtr::nullopt;
            VTR_LOG("ROUTECAST_PRERELEASE net=%zu name=%s\\n",size_t(net),net_list.net_name(net).c_str());
        }
    }
'''+needle);source='#include <fstream>\n#include <unordered_set>\n'+source;(out/'route.cpp').write_text(source);obj=out/'route.o'
with (out/'compile.log').open('w') as f:subprocess.run([*p['compile'][:-4],'-c',str(out/'route.cpp'),'-o',str(obj)],stdout=f,stderr=subprocess.STDOUT,check=True)
archive=out/'libvpr.a';shutil.copyfile(dirty/'libvpr.a',archive);exe=out/'repair_vpr';link=[str(archive) if x.endswith('/libvpr.a') else str(exe) if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link[1:1]=[str(base/(n+'.o')) for n in ('read_route','old_traceback')]+[str(obj),str(dirty/'route_net.o')]
with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True)
(out/'receipt.json').write_text(json.dumps({'binary_sha256':sha(exe),'source_sha256':sha(out/'route.cpp'),'inputs_sha256':{x:sha(x) for x in link if x.endswith(('.o','.a'))},'scope':'Private fresh serial seeded process; all listed trees released once after seed STA. No rollback or production thread safety.'},indent=2)+'\n');print('built')
