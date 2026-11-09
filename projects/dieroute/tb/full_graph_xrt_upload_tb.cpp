// Real immutable graph transfer plus a directed native-edge device test.
// This is not an online cohort search or a full routing/QoR result.
#include "../host/xrt_device_context.hpp"
#include "native_csr_io.hpp"
#include "net_commit_hbm.hpp"
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <vector>
using namespace dieroute;
using U=std::uint64_t;using N=std::uint32_t;
void require(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
int main(int argc,char** argv){try{
 require(argc==10,"usage: upload_probe POLICY OFFSETS ARCS ARCH GROUP ROOT CHILD PIP NET");
 auto arch=native::fingerprint(argv[4]);native::Container policy(argv[1],0x44520026,8,arch),offsets(argv[2],native::offsets_type,8,arch),arcs(argv[3],native::arcs_type,8,arch);
 require(policy.count<UINT32_MAX&&offsets.count==policy.count+1&&offsets.offset(0)==0&&offsets.offset(policy.count)==arcs.count,"graph shape");
 N root=std::stoul(argv[6]),child=std::stoul(argv[7]),pip=std::stoul(argv[8]),net=std::stoul(argv[9]);require(root<policy.count&&child<policy.count&&root!=child&&pip!=UINT32_MAX,"native edge domain");
 auto allowed=[&](N node){auto p=native::le64(policy.data+U(node)*8);return !(p>>41)&&((p>>32)&255)&&!(((p>>32)&255)>>3)&&!(p&(U(1)<<40))&&(N(p)==UINT32_MAX||N(p)==net);};
 require(allowed(root)&&allowed(child),"selected native edge permission");bool edge=false;
 for(U i=offsets.offset(root);i<offsets.offset(root+1);++i){if(arcs.dst(i)==child&&arcs.edge(i)==pip)edge=true;require(arcs.dst(i)!=child||arcs.edge(i)!=UINT32_MAX,"bad PIP fixture is present in CSR");}
 require(edge,"selected native PIP absent from CSR");
 auto& ctx=xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");xrt::kernel kernel(ctx.device,ctx.uuid,"dieroute_net_commit_hbm:{net_commit}",xrt::kernel::cu_access_mode::exclusive);
 std::array<xrt::bo,15> b;std::array<U,15> bytes={128,policy.payload,offsets.payload,arcs.payload,32,64,64,16,48*64,64*64,2*64,64,128*128,32*64,64};
 for(unsigned i=0;i<15;++i){auto group=kernel.group_id(i);if(i>=1&&i<=3)require(U(group)==std::stoull(argv[5]),"runtime graph group");b[i]=xrt::bo(ctx.device,bytes[i],group);}
 for(unsigned i=1;i<=3;++i)for(unsigned j=1;j<i;++j)require(b[i].address()+bytes[i]<=b[j].address()||b[j].address()+bytes[j]<=b[i].address(),"graph allocation alias");
 constexpr U chunk=16*1024*1024;std::array<const unsigned char*,3> data={policy.data,offsets.data,arcs.data};
 for(unsigned i=1;i<=3;++i)for(U off=0;off<bytes[i];off+=chunk){U n=std::min(chunk,bytes[i]-off);b[i].write(data[i-1]+off,n,off);b[i].sync(XCL_BO_SYNC_BO_TO_DEVICE,n,off);if((off+n)%(128*1024*1024)==0||off+n==bytes[i])std::cerr<<"UPLOAD buffer="<<i<<" bytes="<<off+n<<'/'<<bytes[i]<<'\n';}
 std::vector<unsigned char> readback(chunk);U verified=0;
 for(unsigned i=1;i<=3;++i)for(U off=0;off<bytes[i];off+=chunk){U n=std::min(chunk,bytes[i]-off);b[i].sync(XCL_BO_SYNC_BO_FROM_DEVICE,n,off);b[i].read(readback.data(),n,off);require(!std::memcmp(readback.data(),data[i-1]+off,n),"native graph readback mismatch");verified+=n;}
 // Authority is zeroed once before initialization, then only the CU writes it.
 for(unsigned i=0;i<15;++i)if(i<1||i>3){std::vector<unsigned char> zero(bytes[i]);b[i].write(zero.data(),zero.size(),0);b[i].sync(XCL_BO_SYNC_BO_TO_DEVICE);}
 std::array<SummaryWord,2> command{};SummaryWord completion{},control{},branch{};std::array<SummaryWord,2> nets{};std::array<SummaryWord,32> deltas{};std::array<U,4> reads{};std::array<U,2> path{};unsigned calls=0;
 auto download=[&](unsigned index,void* target,U n){b[index].sync(XCL_BO_SYNC_BO_FROM_DEVICE,n,0);b[index].read(target,n,0);};
 auto request=[&](U op){command={};command[0].w[0]=1;command[0].w[1]=op;command[0].w[2]=control.w[1];command[0].w[3]=0;command[0].w[4]=net;command[0].w[5]=nets[0].w[0]==1?nets[0].w[5]:0;command[0].w[6]=1;};
 auto run=[&](U expected){
  b[0].write(command.data(),128,0);b[0].sync(XCL_BO_SYNC_BO_TO_DEVICE,128,0);
  auto execution=kernel(b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],b[11],b[12],b[13],b[14],N(policy.count),arcs.count,3u,16u,2u,64u,2u,1u,1u,1u,128u,32u);
  require(execution.wait()==ERT_CMD_STATE_COMPLETED,"CU did not complete");download(14,&completion,64);download(11,&control,64);download(10,nets.data(),128);require(completion.w[7]<=32,"delta overflow");if(completion.w[7])download(13,deltas.data(),completion.w[7]*64);++calls;
  std::cerr<<"XRT_REAL_GRAPH call="<<calls<<" op="<<command[0].w[1]<<" status="<<completion.w[0]<<" reads="<<completion.w[2]<<" deltas="<<completion.w[7]<<" authority_nonzero_host_uploads=0\n";require(completion.w[0]==expected,"unexpected directed CU status");
 };
 request(commit_initialize);command[0].w[4]=0;run(commit_ok);request(commit_start);command[0].w[7]=root;run(commit_ok);
 auto authority=[&](){std::vector<unsigned char> image;for(unsigned i:{8u,9u,10u,11u}){auto old=image.size();image.resize(old+bytes[i]);download(i,image.data()+old,bytes[i]);}return image;};
 auto propose=[&](N key){request(commit_proposal);command[1].w[0]=2;command[1].w[2]=1;command[1].w[3]=1;
  reads=root<child?std::array<U,4>{root,1,child,0}:std::array<U,4>{child,0,root,1};branch={};branch.w[0]=root;branch.w[1]=child;branch.w[3]=1;branch.w[4]=1;branch.w[5]=1;path={child|(U(key)<<32),0};
  b[4].write(reads.data(),32,0);b[4].sync(XCL_BO_SYNC_BO_TO_DEVICE,32,0);b[6].write(&branch,64,0);b[6].sync(XCL_BO_SYNC_BO_TO_DEVICE,64,0);b[7].write(path.data(),16,0);b[7].sync(XCL_BO_SYNC_BO_TO_DEVICE,16,0);
 };
 auto before=authority();propose(UINT32_MAX);run(commit_bad_path);require(authority()==before&&completion.w[7]==0,"rejected PIP changed authority");
 auto query=[&](N node,U occupancy,U version,U member){request(commit_query);command[0].w[7]=node;run(commit_ok);require(completion.w[7]==1&&N(deltas[0].w[1])==node&&deltas[0].w[2]==occupancy&&deltas[0].w[4]==version&&deltas[0].w[7]==member,"directed membership query mismatch");};
 query(child,0,0,0);propose(pip);run(commit_ok);query(root,1,1,1);query(child,1,1,1);require(calls==7,"directed call accounting");
 std::cout<<"REAL_GRAPH_PROBE_PASS verified_bytes="<<verified<<" kernel_calls="<<calls<<" root="<<root<<" child="<<child<<" pip="<<pip<<" net="<<net<<" authority_nonzero_host_uploads=0 full_cohort_routing=0\n";
}catch(const std::exception& e){std::cerr<<"REAL_GRAPH_PROBE_FAIL "<<e.what()<<'\n';return 1;}}
