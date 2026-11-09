#include "native_csr_io.hpp"
#include "native_search_hbm_csr.hpp"
#include <iostream>
#include <vector>
using namespace dieroute;using namespace dieroute::native;
int main(int argc,char** argv){try{
 check(argc==6,"usage: probe_native_hbm_csr SEARCH POLICY ARCH FOOTPRINT MAPPING");auto arch=fingerprint(argv[3]);fs::path search=argv[1];Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),policy(argv[2],0x44520026,8,arch);Raw tasks(fs::path(argv[4])/"tasks.bin",8),mapping(fs::path(argv[5])/"footprint_node_map.bin",1);
 check(offsets.count==policy.count+1&&policy.count<UINT32_MAX,"graph coverage");
 std::uint64_t cases=0,total_visits=0,total_allowed=0;
 for(unsigned task=0;task<100;++task)for(unsigned endpoint:{2u,3u}){
  auto source=mapping.at(tasks.at(task,endpoint),0),net=tasks.at(task,1);check(source<policy.count,"mapped node range");auto begin=offsets.offset(source),end=offsets.offset(source+1);check(begin<=end&&end<=arcs.count,"row range");std::vector<NativeCSRArc> expected;
  for(auto i=begin;i<end;++i){auto dst=arcs.dst(i),edge=arcs.edge(i);check(dst<policy.count,"destination range");auto p=le64(policy.data+dst*8);if((p&(std::uint64_t(1)<<40))||(std::uint32_t(p)!=UINT32_MAX&&std::uint32_t(p)!=net))continue;auto mask=unsigned((p>>32)&255),owner=0u;check(mask>0&&mask<8&&!(p>>41),"policy topology");while(!(mask&(1u<<owner)))++owner;expected.push_back({dst,edge,owner,mask});}
  for(std::uint64_t budget:{1,7,64}){std::uint64_t cursor=begin,visited=0,seen=0,count=0;NativeCSRArc out{};
   while(true){auto status=native_search_next_arc<134217728,536870912>(reinterpret_cast<const std::uint64_t*>(offsets.data),reinterpret_cast<const std::uint64_t*>(arcs.data),reinterpret_cast<const std::uint64_t*>(policy.data),policy.count,arcs.count,3,source,net,budget,cursor,visited,out);check(status!=NativeCSRStatus::invalid,"scanner rejected native row");check(visited<=budget,"visit budget");count+=visited;
    if(status==NativeCSRStatus::arc){check(seen<expected.size(),"extra arc");auto e=expected[seen++];check(out.node==e.node&&out.edge==e.edge&&out.owner==e.owner&&out.membership==e.membership,"arc differential mismatch");}
    if(status==NativeCSRStatus::end)break;
   }
   check(cursor==end&&count==end-begin&&seen==expected.size(),"row completion/accounting");++cases;total_visits+=count;total_allowed+=seen;
  }
 }
 std::cout<<"{\"status\":\"passed\",\"cases\":"<<cases<<",\"visits\":"<<total_visits<<",\"allowed_arcs\":"<<total_allowed<<",\"scope\":\"First100tasks both endpoints, budgets1/7/64, real immutable CSR and policy; CPU traversal differential only\"}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
