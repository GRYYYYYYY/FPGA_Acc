"""Compile actual extracted production PressureGuard against deterministic mocks."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];H=R/'build/native_external_net2_pressure_intervention_v1_2026-10-19/source/overlay/SerialNetlistRouter.tpp';D=R/'experiments/net2_pressure_guard_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);text=H.read_text();a=text.index('        struct PressureGuard {');b=text.index('        std::unique_ptr<PressureGuard> pressure;',a);guard=text[a:b]
 prefix=r'''
#include <algorithm>
#include <cstdio>
#include <memory>
#include <optional>
#include <stdexcept>
#include <vector>
#include <cassert>
#include <random>
using RRNodeId=int;using ParentNetId=int;
enum {CHANX,CHANY,SOURCE};
struct Node {int inode;};struct Tree {std::vector<Node> all_nodes()const{return {{0}};}};
struct Inf {int value=0;int occ()const{return value;}void set_occ(int x){value=x;}};
struct Ctx {std::vector<Inf> rr_node_route_inf=std::vector<Inf>(4);std::vector<std::optional<Tree>> route_trees={Tree{}};};
struct Graph {std::vector<int> nodes()const{return {0,1,2,3};}int node_type(int n)const{return n==3?SOURCE:CHANX;}};
struct Device {Graph rr_graph;};struct Global {Ctx ctx;Device dev;Ctx& mutable_routing(){return ctx;}const Device& device()const{return dev;}} g_vpr_ctx;
#define VTR_LOG(...) ((void)0)
void input(const std::vector<int>& expected,const std::vector<int>& desired,int rows=3){FILE*f=std::fopen("pressure.tsv","w");for(int i=0;i<rows;i++)std::fprintf(f,"%d %d %d\n",i,expected[i],desired[i]);std::fclose(f);}
void set(const std::vector<int>& values){for(int i=0;i<3;i++)g_vpr_ctx.ctx.rr_node_route_inf[i].set_occ(values[i]);}
void same(const std::vector<int>& values){for(int i=0;i<3;i++)assert(g_vpr_ctx.ctx.rr_node_route_inf[i].occ()==values[i]);}
'''
 suffix=r'''
int main(){std::mt19937 rng(20261019);int trials=0;
for(int i=0;i<300;i++){
 std::vector<int> e={1+int(rng()%5),int(rng()%5),int(rng()%5)},d={1+int(rng()%5),int(rng()%5),int(rng()%5)};
 set(e);input(e,e);{PressureGuard p(0);same(e);p.restore();p.restore();}same(e);
 set(e);input(e,d);{PressureGuard p(0);same(d);g_vpr_ctx.ctx.rr_node_route_inf[0].value--;g_vpr_ctx.ctx.rr_node_route_inf[2].value++;p.restore();}auto result=e;result[0]--;result[2]++;same(result);
 set(e);input(e,d);try{PressureGuard p(0);throw std::runtime_error("injected");}catch(const std::runtime_error&){}same(e);
 set(e);auto stale=e;stale[1]++;input(stale,d);bool failed=false;try{PressureGuard p(0);}catch(const std::runtime_error&){failed=true;}assert(failed);same(e);
 set(e);input(e,d,2);failed=false;try{PressureGuard p(0);}catch(const std::runtime_error&){failed=true;}assert(failed);same(e);
 set(e);auto invalid=d;invalid[0]=0;input(e,invalid);failed=false;try{PressureGuard p(0);}catch(const std::runtime_error&){failed=true;}assert(failed);same(e);
 set(e);invalid=d;invalid[1]=-1;input(e,invalid);failed=false;try{PressureGuard p(0);}catch(const std::runtime_error&){failed=true;}assert(failed);same(e);trials++;
}
std::printf("PRESSURE_GUARD_CONTRACT_PASS %d\n",trials);}
'''
 source=D/'contract.cpp';source.write_text(prefix+guard+suffix);binary=D/'contract';subprocess.run(['/usr/bin/c++','-std=c++17','-O2',str(source),'-o',str(binary)],check=True);run=subprocess.run([str(binary)],cwd=D,text=True,capture_output=True,check=True);print(run.stdout.strip());(D/'verification.json').write_text(json.dumps(dict(status='ACTUAL_EXTRACTED_PRESSURE_GUARD_300_RANDOM_FIXTURES_PASS',fixtures=300,checks=['own-pressure idempotence','offset restoration after simulated native tree replacement','exception scope restoration','stale count rejected before mutation','incomplete domain rejected before mutation','missing own occupancy rejected','negative pressure rejected'],bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [H,source,binary,Path(__file__).resolve()]},scope='Actual guard compiled with mock native graph/context. No native search equivalence or full routing rollback claim.'),indent=2)+'\n')
if __name__=='__main__':main()
