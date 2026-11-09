// Actual whole-search and seed CUs on full native CSR and imported authority.
#include "../host/xrt_device_context.hpp"
#include "native_csr_io.hpp"
#include "native_quotient.hpp"
#include "native_search_hbm_labels.hpp"
#include "native_search_hbm_queue.hpp"
#include "native_search_hbm_cost.hpp"
#include "summary_hbm.hpp"
#include <array>
#include <cstring>
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <iostream>
#include <memory>
using namespace dieroute;
using namespace dieroute::native;
using U=std::uint64_t;
void raw(const fs::path& p,const void* data,size_t n){std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),n);check(bool(f),"artifact write");}
int main(int argc,char** argv){try{
 check(argc==10||argc==11,"usage: native_xrt SNAP SEARCH POLICY ARCH SLOT SINK LABELS EXPANSIONS OUT [QUOTIENT]");fs::path snap=argv[1],search=argv[2],out=argv[9];check(!fs::exists(out),"output exists");auto arch=fingerprint(argv[4]);auto slot=std::stoul(argv[5]),sink=std::stoul(argv[6]),cap=std::stoul(argv[7]);auto limit=std::stoull(argv[8]);check(cap&&cap<=2097152,"label capacity");
 Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),policy(argv[3],0x44520026,8,arch);
 Mapping rm(snap/"resources.raw"),tm(snap/"trees.raw"),nm(snap/"nets.raw"),cm(snap/"control.raw"),sm(snap/"tree_seeds.raw");check(cm.bytes==64&&sm.bytes%64==0&&slot<nm.bytes/64,"snapshot shape");SummaryWord control{},net{};std::memcpy(&control,cm.data,64);std::memcpy(&net,nm.data+slot*64,64);
 auto nodes=std::uint32_t(control.w[5]),dies=std::uint32_t(control.w[5]>>32),shard=std::uint32_t(control.w[6]),tree=std::uint32_t(control.w[7]);check(offsets.count==U(nodes)+1&&policy.count==nodes&&sink<nodes&&net.w[0]==control.w[0]&&sm.bytes/64==net.w[4],"native shape");
 std::vector<U> potential;std::unique_ptr<QuotientPotential> quotient;
 if(argc==11){quotient=std::make_unique<QuotientPotential>(argv[10],arch,nodes);quotient->prepare(sink,std::uint32_t(le64(sm.data+8)));potential.resize(nodes);for(std::uint32_t n=0;n<nodes;++n)potential[n]=std::min<U>((*quotient)(n),nodes);check(potential[sink]==0,"sink potential");
  auto allowed=[&](std::uint32_t n){check(n<nodes,"CSR destination");auto p=le64(policy.data+U(n)*8);return !(p&(U(1)<<40))&&(std::uint32_t(p)==UINT32_MAX||std::uint32_t(p)==net.w[1]);};U checked=0;
  for(std::uint32_t n=0;n<nodes;++n)if(allowed(n))for(auto i=offsets.offset(n);i<offsets.offset(n+1);++i){auto dst=arcs.dst(i);if(allowed(dst)){check(potential[n]<=potential[dst]+1,"potential consistency");++checked;}}std::cerr<<"potential consistency edges="<<checked<<'\n';
 }
 auto& ctx=xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");xrt::kernel snapshot(ctx.device,ctx.uuid,"dieroute_native_snapshot_search_hbm:{snapshot_search}",xrt::kernel::cu_access_mode::exclusive),worker(ctx.device,ctx.uuid,"dieroute_native_search_worker_hbm:{search_worker}",xrt::kernel::cu_access_mode::exclusive),commit(ctx.device,ctx.uuid,"dieroute_net_commit_hbm:{net_commit}",xrt::kernel::cu_access_mode::exclusive);
 const unsigned qcap=std::max<unsigned>(1024,cap*4),jcap=std::max<unsigned>(1024,cap*16);std::array<xrt::bo,13> b;std::array<U,13> sizes={offsets.payload,arcs.payload,policy.payload,rm.bytes,64,potential.empty()?64:potential.size()*8,U(cap)*64,U(qcap)*64,U(jcap)*64,64,128,64,64};
 for(unsigned i=0;i<13;++i)b[i]=xrt::bo(ctx.device,sizes[i],snapshot.group_id(i));
 for(auto [s,c]:std::array<std::pair<unsigned,unsigned>,5>{{{0,2},{1,3},{2,1},{3,8},{4,11}}})check(snapshot.group_id(s)==commit.group_id(c),"commit shared groups");
 for(auto [w,s]:std::array<std::pair<unsigned,unsigned>,4>{{{0,6},{1,7},{2,8},{5,9}}})check(worker.group_id(w)==snapshot.group_id(s),"seed shared groups");
 xrt::bo trees(ctx.device,tm.bytes,commit.group_id(9)),nets(ctx.device,nm.bytes,commit.group_id(10)),parent(ctx.device,64,worker.group_id(3)),observation(ctx.device,64,worker.group_id(4)),frontier(ctx.device,64,worker.group_id(17));
 constexpr U chunk=16*(1<<20);std::vector<unsigned char> buffer(chunk);U transferred=0;
 auto transfer=[&](xrt::bo& bo,const unsigned char* data,U bytes,bool verify){for(U off=0;off<bytes;off+=chunk){auto n=std::min(chunk,bytes-off);bo.write(data+off,n,off);bo.sync(XCL_BO_SYNC_BO_TO_DEVICE,n,off);}if(verify)for(U off=0;off<bytes;off+=chunk){auto n=std::min(chunk,bytes-off);bo.sync(XCL_BO_SYNC_BO_FROM_DEVICE,n,off);bo.read(buffer.data(),n,off);check(!std::memcmp(buffer.data(),data+off,n),"native upload readback");transferred+=n;}};
 transfer(b[0],offsets.data,sizes[0],true);transfer(b[1],arcs.data,sizes[1],true);transfer(b[2],policy.data,sizes[2],true);if(!potential.empty())transfer(b[5],reinterpret_cast<const unsigned char*>(potential.data()),sizes[5],true);else{std::array<U,8> z{};transfer(b[5],reinterpret_cast<const unsigned char*>(z.data()),64,false);}
 transfer(b[3],rm.data,rm.bytes,true);transfer(b[4],cm.data,64,true);transfer(trees,tm.data,tm.bytes,true);transfer(nets,nm.data,nm.bytes,true);std::cerr<<"native initialization verified_bytes="<<transferred<<" authority_imports=1\n";
 std::fill(buffer.begin(),buffer.end(),0);for(unsigned i:{6u,7u,8u,9u,10u,11u,12u})for(U off=0;off<sizes[i];off+=chunk){auto n=std::min(chunk,sizes[i]-off);b[i].write(buffer.data(),n,off);b[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,n,off);}observation.write(buffer.data(),64,0);observation.sync(XCL_BO_SYNC_BO_TO_DEVICE);
 std::array<U,8> meta{},result{},goal{};unsigned calls=0;
 for(U i=0;i<sm.bytes/64;++i){auto seednode=std::uint32_t(le64(sm.data+i*64+8)),depth=std::uint32_t(le64(sm.data+i*64+40));NativeSearchLabelSlot seed{};seed.epoch=1;seed.cost=0;seed.node=seednode;seed.hops=depth;parent.write(&seed,64,0);parent.sync(XCL_BO_SYNC_BO_TO_DEVICE);
  auto run=worker(b[6],b[7],b[8],parent,observation,b[9],unsigned(cap),qcap,jcap,0u,0u,control.w[0],0u,control.w[2],potential.empty()?U(0):potential[seednode],UINT64_MAX,1u,frontier,4u);check(run.wait()==ERT_CMD_STATE_COMPLETED,"seed completion");++calls;b[9].sync(XCL_BO_SYNC_BO_FROM_DEVICE);b[9].read(meta.data());check(meta[2]==0&&meta[0]==i+1,"complete tree seed initialization");
 }
 meta[2]=sm.bytes/64;b[9].write(meta.data());b[9].sync(XCL_BO_SYNC_BO_TO_DEVICE);std::array<U,16> cfg={nodes,arcs.count,dies,shard,tree,net.w[1],sink,control.w[0],control.w[1],1,limit,UINT32_MAX,cap,qcap,jcap,U(!potential.empty())};b[10].write(cfg.data());b[10].sync(XCL_BO_SYNC_BO_TO_DEVICE);
 auto run=snapshot(b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],b[11],b[12]);check(run.wait()==ERT_CMD_STATE_COMPLETED,"native search completion");b[11].sync(XCL_BO_SYNC_BO_FROM_DEVICE);b[11].read(result.data());b[12].sync(XCL_BO_SYNC_BO_FROM_DEVICE);b[12].read(goal.data());b[9].sync(XCL_BO_SYNC_BO_FROM_DEVICE);b[9].read(meta.data());check(meta[1]<=jcap&&result[0]<=6,"result bounds");
 auto preserved=[&](xrt::bo& bo,const unsigned char* data,U bytes){for(U off=0;off<bytes;off+=chunk){auto n=std::min(chunk,bytes-off);bo.sync(XCL_BO_SYNC_BO_FROM_DEVICE,n,off);bo.read(buffer.data(),n,off);check(!std::memcmp(buffer.data(),data+off,n),"native search mutated authority");}};preserved(b[3],rm.data,rm.bytes);preserved(b[4],cm.data,64);preserved(trees,tm.data,tm.bytes);preserved(nets,nm.data,nm.bytes);
 fs::create_directories(out);raw(out/"result.raw",result.data(),64);raw(out/"goal.raw",goal.data(),64);raw(out/"metadata.raw",meta.data(),64);std::vector<NativeSearchResourceObservation> journal(meta[1]);if(meta[1]){b[8].sync(XCL_BO_SYNC_BO_FROM_DEVICE,meta[1]*64,0);b[8].read(journal.data(),meta[1]*64,0);}raw(out/"observations.raw",journal.data(),journal.size()*64);
 if(result[0]==0){std::vector<NativeSearchLabelSlot> labels(cap);b[6].sync(XCL_BO_SYNC_BO_FROM_DEVICE);b[6].read(labels.data());std::vector<std::uint32_t> path,pips;auto n=unsigned(sink);for(U i=0;;++i){check(i<=meta[2],"trace cycle");auto loc=native_search_label_lookup<33554432>(labels.data(),cap,1,n);check(loc.status==NativeLabelLookup::found,"trace missing");auto l=labels[loc.slot];if(l.parent==UINT32_MAX){U attachment=n;raw(out/"attachment.raw",&attachment,8);break;}path.push_back(n);pips.push_back(l.edge);n=l.parent;}std::reverse(path.begin(),path.end());std::reverse(pips.begin(),pips.end());raw(out/"path_nodes.raw",path.data(),path.size()*4);raw(out/"path_pips.raw",pips.data(),pips.size()*4);}
 std::cout<<"{\"status\":\"executed\",\"search_status\":"<<result[0]<<",\"seed_calls\":"<<calls<<",\"snapshot_calls\":1,\"expanded\":"<<result[1]<<",\"observations\":"<<meta[1]<<",\"cost\":"<<goal[1]<<",\"verified_upload_bytes\":"<<transferred<<",\"authority_imports\":1,\"authority_reuploads\":0,\"scope\":\"Actual native whole-search CU on imported immutable authority; no full routing, commit execution or board claim\"}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
