"""Private once-per-NET dirty-seed repair; unchanged shared VPR inputs."""
import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';base=root/'build/native_search_seed_v3_2026-10-06';out=root/'build/capacity_dirty_repair_2026-10-06';out.mkdir();protocol=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());source=(shared/'vpr/src/route/route_net.cpp').read_text();needle='    const RouteTree& tree = route_ctx.route_trees[net_id].value();';assert source.count(needle)==1
source=source.replace(needle,'''    // Experimental first-iteration whole-NET repair list, matched by NET name.
    // Used only in the fresh single-task process harness, not a transaction API.
    const char* repair_path = std::getenv("ROUTECAST_REPAIR_NET_NAMES");
    static thread_local std::unordered_set<std::string> selected;
    static thread_local std::unordered_set<std::string> visited;
    static thread_local bool loaded = false;
    if (repair_path && !loaded) {
        std::ifstream file(repair_path);
        if (!file) throw std::runtime_error("repair list open failed");
        std::string name; while (std::getline(file,name)) if (!name.empty()) selected.insert(name);
        loaded = true;
    }
    if (repair_path && selected.count(net_list.net_name(net_id)) && visited.insert(net_list.net_name(net_id)).second) {
        VTR_LOG("ROUTECAST_DIRTY_REPAIR net=%zu name=%s\\n",size_t(net_id),net_list.net_name(net_id).c_str());
        return true;
    }
'''+needle)
source='#include <cstdlib>\n#include <fstream>\n#include <unordered_set>\n#include <stdexcept>\n'+source;(out/'route_net.cpp').write_text(source);obj=out/'route_net.o';cmd=[*protocol['compile'][:-4],'-c',str(out/'route_net.cpp'),'-o',str(obj)]
with (out/'compile.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
archive=out/'libvpr.a';shutil.copyfile(base/'libvpr.a',archive);subprocess.run(['ar','d',str(archive),'route_net.cpp.o'],check=True);binary=out/'repair_vpr';link=[str(archive) if x.endswith('/libvpr.a') else str(binary) if x.endswith('/routecast_seed_vpr') else x for x in protocol['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link[1:1]=[str(base/(n+'.o')) for n in ('read_route','old_traceback','route')]+[str(obj)]
with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True)
(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(out/'route_net.cpp'),'builder_sha256':sha(Path(__file__)),'binary_sha256':sha(binary),'link_inputs_sha256':{x:sha(x) for x in link if x.endswith(('.a','.o'))},'scope':'Fresh-process dirty whole-NET repair only; list checked before incomplete/overflow tests, fixed/ignored guards preserved; does not guarantee timing improvement or exception-safe publication.'},indent=2)+'\n');print('built',binary)
