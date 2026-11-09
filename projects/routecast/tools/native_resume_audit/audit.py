"""Bind concrete upstream reset sites before implementing native resume."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
UP=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src'
rules=[('route/route_common.cpp','std::fill(route_ctx.route_trees.begin(), route_ctx.route_trees.end(), vtr::nullopt);','init_route_structs clears all trees; loading must occur after this reset'),('route/route_net.cpp','num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1 || ripup_high_fanout_nets','setup_net rebuild branch includes first iteration and low fanout; loading alone cannot preserve processed NETs'),('route/route_net.cpp','tree = vtr::nullopt;','rebuild branch discards existing NET tree after subtracting occupancy'),('route/route.cpp','init_net_delay_from_lookahead(*router_lookahead,','initial timing uses lookahead instead of loaded path delay'),('base/read_route.cpp','recompute_occupancy_from_scratch(router_net_list,','route loader reconstructs occupancy; state must be synchronized after partial NET removal'),('base/read_route.cpp','init_route_structs(router_net_list,','loader itself resets routing structures; never invoke it during recursive initialization'),('base/vpr_api.cpp','if (router_opts.doRouting == STAGE_DO)','CLI selects route computation separately from load stage')]
rows=[];bindings={str(Path(__file__)):sha(Path(__file__))}
for name,needle,meaning in rules:
    file=UP/name;lines=file.read_text().splitlines();hits=[i for i,line in enumerate(lines) if needle in line]
    assert hits, (name,needle)
    bindings[str(file)]=sha(file)
    rows.append(dict(path=str(file),needle=needle,lines=[i+1 for i in hits],context=[lines[max(0,i-3):i+5] for i in hits],consequence=meaning))
assert all(sha(p)==h for p,h in bindings.items())
out=ROOT/'experiments/native_resume_source_audit_2026-10-07';out.mkdir(exist_ok=False)
(out/'audit.json').write_text(json.dumps(dict(bindings=bindings,sites=rows,scope='Static evidence of concrete tree/occupancy/timing resets in current upstream source. No compiled resume implementation or new native execution. Guides private modifications; shared source untouched.'),indent=2)+'\n')
print('verified reset sites',len(rows))
