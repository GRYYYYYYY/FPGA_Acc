"""Own corrected native link, read-only source-final history exporter."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19';N=R/'build/native_external_shared_sink_native_v1_2026-10-19';D=R/'build/native_source_final_history_observer_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 b=json.loads((B/'receipt.json').read_text());n=json.loads((N/'receipt.json').read_text());assert all(sha(k)==h for k,h in b['bindings'].items()) and all(sha(k)==h for k,h in n['bindings'].items());assert sha(N/'sequence_vpr')==n['binary_sha256'];D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/route.cpp';s=f.read_text();anchor='    return success;';assert s.count(anchor)==1
 code=r'''
    if(success && std::getenv("ROUTECAST_EXPORT_SOURCE_FINAL_HISTORY")) {
        FILE* history=std::fopen("source_final_rr_history.tsv","wx");
        if(!history)throw std::runtime_error("source history open");
        std::fprintf(history,"F\tSOURCE_ROUTER_END_AFTER_BEST_RESTORE\t%d\n",itry);
        const auto& graph=g_vpr_ctx.device().rr_graph;
        for(auto id:graph.nodes()) {
            const auto value=route_ctx.rr_node_route_inf[id].acc_cost;
            static_assert(sizeof(value)==sizeof(uint32_t),"history float width");
            uint32_t bits;std::memcpy(&bits,&value,sizeof(bits));
            std::fprintf(history,"N\t%zu\t%d\t%d\t%08x\t%a\n",size_t(id),int(graph.node_capacity(id)),route_ctx.rr_node_route_inf[id].occ(),unsigned(bits),double(value));
        }
        bool failed=std::ferror(history);if(std::fclose(history))failed=true;
        if(failed)throw std::runtime_error("source history export failed");
    }
'''
 s='#include <cstdint>\n#include <cstring>\n'+s.replace(anchor,code+anchor);f.write_text(s);bp=json.loads((B/'protocol.json').read_text());np=json.loads((N/'protocol.json').read_text());compile=[x.replace(str(B),str(D)) for x in bp['compile']];link=[str(D/'route.o') if x==str(B/'route.o') else str(D/'sequence_vpr') if x==str(N/'sequence_vpr') else x for x in np['link']];bindings={str(Path(__file__)):sha(__file__),str(B/'receipt.json'):sha(B/'receipt.json'),str(N/'receipt.json'):sha(N/'receipt.json')}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for p in (D/'source').rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Source-only explicit env export after successful full native route and best-tree restore. End-of-run negotiated acc_cost is not historical state of best iteration. Exact f32 bits plus hexadecimal double; no mutation or target source mixing. Runtime source parity pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='SOURCE_FINAL_HISTORY_OBSERVER_BUILT_RUNTIME_PARITY_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('SOURCE_FINAL_HISTORY_OBSERVER_BUILT_RUNTIME_PARITY_PENDING',flush=True)
if __name__=='__main__':main()
