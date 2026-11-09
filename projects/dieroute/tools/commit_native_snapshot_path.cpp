#include "native_csr_io.hpp"
#include "net_commit_hbm.hpp"
#include <algorithm>
#include <iostream>
#include <map>
#include <vector>
using namespace dieroute;
using namespace dieroute::native;
template<class T> std::vector<T> load(const fs::path& p){Mapping m(p);check(m.bytes%sizeof(T)==0,"raw width");std::vector<T> v(m.bytes/sizeof(T));std::memcpy(v.data(),m.data,m.bytes);return v;}
template<class T> void save(const fs::path& p,const std::vector<T>& v){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));check(bool(f),"write");}
int main(int argc,char** argv){try{
 check(argc==8,"usage: commit SNAPSHOT ARTIFACT SEARCH POLICY ARCH NET_SLOT OUT");fs::path snap=argv[1],art=argv[2],out=argv[7];check(!fs::exists(out),"output exists");auto arch=fingerprint(argv[5]);auto slot=std::stoul(argv[6]);
 Container offsets(fs::path(argv[3])/"offsets.bin",offsets_type,8,arch),arcs(fs::path(argv[3])/"arcs.bin",arcs_type,8,arch),policy(argv[4],0x44520026,8,arch);
 auto resources=load<SummaryWord>(snap/"resources.raw"),trees=load<SummaryWord>(snap/"trees.raw"),nets=load<SummaryWord>(snap/"nets.raw"),control=load<SummaryWord>(snap/"control.raw");auto goal=load<std::uint64_t>(art/"goal.raw"),attachment=load<std::uint64_t>(art/"attachment.raw");auto nodes=load<std::uint32_t>(art/"path_nodes.raw"),pips=load<std::uint32_t>(art/"path_pips.raw");auto observations=load<SummaryWord>(art/"observations.raw");
 check(slot<nets.size()&&control.size()==1&&goal.size()==8&&attachment.size()==1&&nodes.size()==pips.size(),"shape");auto oldnet=nets[slot];auto oldctl=control[0];check(oldnet.w[0]==oldctl.w[0],"session");
 std::map<std::uint64_t,std::uint64_t> canonical;for(auto o:observations){check(o.w[4]==oldctl.w[0]&&o.w[5]==goal[0],"observation handoff");auto inserted=canonical.emplace(o.w[0],o.w[1]);check(inserted.second||inserted.first->second==o.w[1],"inconsistent observation versions");}
 std::vector<std::uint64_t> reads;for(auto [node,version]:canonical){reads.push_back(node);reads.push_back(version);}if(reads.empty())reads.resize(2);
 std::vector<std::uint64_t> paths(std::max<size_t>(2,nodes.size()*2));for(size_t i=0;i<nodes.size();++i)paths[i*2]=nodes[i]|(std::uint64_t(pips[i])<<32);
 SummaryWord command[2]{},shadow{},branch{{attachment[0],goal[3],0,nodes.size(),goal[4],goal[1],0,0}},done{};
 command[0]={{oldctl.w[0],commit_proposal,oldctl.w[1],slot,oldnet.w[1],oldnet.w[5],oldctl.w[2],0}};command[1].w[0]=canonical.size();command[1].w[2]=1;command[1].w[3]=nodes.size();
 auto scratch_cap=std::uint32_t(std::max<size_t>(256,nodes.size()*4+16)),delta_cap=std::uint32_t(std::max<size_t>(64,nodes.size()));std::vector<SummaryWord> scratch(scratch_cap*2),deltas(delta_cap);
 auto invoke=[&](){dieroute_net_commit_hbm(command,reinterpret_cast<const std::uint64_t*>(policy.data),reinterpret_cast<const std::uint64_t*>(offsets.data),reinterpret_cast<const std::uint64_t*>(arcs.data),reads.data(),&shadow,&branch,paths.data(),resources.data(),trees.data(),nets.data(),control.data(),scratch.data(),deltas.data(),&done,policy.count,arcs.count,oldctl.w[5]>>32,std::uint32_t(oldctl.w[6]),nets.size(),trees.size(),reads.size()/2,1,1,paths.size()/2,scratch_cap,delta_cap);};
 invoke();check(done.w[0]==commit_ok&&control[0].w[1]==oldctl.w[1]+1&&nets[slot].w[4]==oldnet.w[4]+nodes.size()&&nets[slot].w[5]==oldnet.w[5]+1,"path commit failed");auto proposal_done=done;
 for(auto node:nodes){command[0]={{control[0].w[0],commit_query,control[0].w[1],slot,nets[slot].w[1],nets[slot].w[5],control[0].w[2],node}};command[1]={};invoke();check(done.w[0]==commit_ok&&done.w[7]==1&&deltas[0].w[7]==1,"published membership missing");}
 fs::create_directories(out);save(out/"resources.raw",resources);save(out/"trees.raw",trees);save(out/"nets.raw",nets);save(out/"control.raw",control);save(out/"proposal_completion.raw",std::vector<SummaryWord>{proposal_done});save(out/"canonical_reads.raw",reads);
 std::cout<<"{\"status\":\"passed\",\"commit_calls\":1,\"query_calls\":"<<nodes.size()<<",\"canonical_reads\":"<<canonical.size()<<",\"published_nodes\":"<<nodes.size()<<",\"revision\":"<<control[0].w[1]<<",\"scope\":\"Actual commit core C-model publication of actual search-top exported native path; no XRT or board claim\"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
