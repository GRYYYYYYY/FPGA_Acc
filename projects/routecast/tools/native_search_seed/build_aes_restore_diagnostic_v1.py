import json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
root=Path.cwd(); base=root/'build/native_candidate_move_accept_scoped_2026-10-06'; original=root/'build/native_candidate_retained_search_2026-10-06/source/route.cpp'
out=root/'build/aes_restore_diagnostic_v1_2026-10-08';out.mkdir();src=out/'route.cpp'
s=original.read_text();needle='''            if (route_ctx.route_trees[net_id])
                pathfinder_update_cost_from_route_tree(route_ctx.route_trees[net_id]->root(), -1);'''
assert s.count(needle)==1
s=s.replace(needle,'''            if (route_ctx.route_trees[net_id]) {
                for (const auto& node : route_ctx.route_trees[net_id]->all_nodes()) {
                    const int occ = route_ctx.rr_node_route_inf[node.inode].occ();
                    if (occ <= 0 || net_list.net_is_ignored(net_id))
                        VTR_LOG("ROUTECAST RESTORE DIAGNOSTIC net=%zu name=%s ignored=%d node=%zu occ=%d\\n",size_t(net_id),net_list.net_name(net_id).c_str(),int(net_list.net_is_ignored(net_id)),size_t(node.inode),occ);
                }
                pathfinder_update_cost_from_route_tree(route_ctx.route_trees[net_id]->root(), -1);
            }''')
src.write_text(s)
p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());shared={f:sha(f) for f in p['inputs_sha256']};obj=out/'route.o'
cmd=[*p['compile'][:-4],'-c',str(src),'-o',str(obj)]
with (out/'compile.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(root/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(obj),str(base/'sync_once.o'),wrap]
with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(f)==h for f,h in shared.items())
(out/'receipt.json').write_text(json.dumps({'original_source_sha256':sha(original),'diagnostic_source_sha256':sha(src),'binary_sha256':sha(out/'sequence_vpr'),'shared_inputs_sha256':shared,'scope':'Logging only before original restore subtraction; original assertions unchanged.'},indent=2)+'\n')
print(out)
