#include "native_search_hbm_labels.hpp"
#include "native_search_hbm_cost.hpp"
#include "summary_hbm.hpp"
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_bo.h>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace dieroute;
using U=std::uint64_t;
static bool state_initialized=false;static U authority_reuploads=0;
static void require(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
template<class T>T read(xrt::bo& bo){T value{};bo.sync(XCL_BO_SYNC_BO_FROM_DEVICE);bo.read(&value,sizeof(value),0);return value;}
template<class T>void command(xrt::bo& bo,const T& value,bool authoritative=false){if(authoritative&&state_initialized)++authority_reuploads;bo.write(&value,sizeof(value),0);bo.sync(XCL_BO_SYNC_BO_TO_DEVICE);}
int main(int argc,char** argv){try{
 require(argc==2,"usage: native_owner_worker_joint_xrt XCLBIN");
 xrt::device device(0);auto uuid=device.load_xclbin(argv[1]);
 xrt::kernel owner(device,uuid,"dieroute_owner_publish_hbm:{owner_die0}",xrt::kernel::cu_access_mode::exclusive);
 xrt::kernel worker(device,uuid,"dieroute_native_search_worker_hbm:{search_worker}",xrt::kernel::cu_access_mode::exclusive);
 xrt::kernel binding(device,uuid,"dieroute_native_search_owner_envelope_hbm:{owner_binding}",xrt::kernel::cu_access_mode::exclusive);
 require(owner.group_id(5)==binding.group_id(0)&&owner.group_id(5)==binding.group_id(1)&&owner.group_id(6)==binding.group_id(0),"publisher/binding groups differ");
 require(binding.group_id(2)==worker.group_id(4),"binding/worker groups differ");
 unsigned initialized=0;
 auto allocate=[&](std::size_t bytes,int group){xrt::bo bo(device,bytes,group);std::vector<unsigned char> zero(bytes,0);bo.write(zero.data());bo.sync(XCL_BO_SYNC_BO_TO_DEVICE);++initialized;return bo;};
 std::array<std::size_t,9> sizes{512,64,64,64,64,512,512,64,64};std::array<xrt::bo,9> ob;
 for(unsigned i=0;i<9;++i)ob[i]=allocate(sizes[i],owner.group_id(i));
 auto labels=allocate(512,worker.group_id(0)),queue=allocate(512,worker.group_id(1)),journal=allocate(512,worker.group_id(2));
 auto seedbo=allocate(64,worker.group_id(3)),observations=allocate(64,worker.group_id(4)),metadata=allocate(64,worker.group_id(5)),current=allocate(64,worker.group_id(17)),status=allocate(64,binding.group_id(3));
 std::array<NativeSearchLabelSlot,8> initial_labels{};command(labels,initial_labels,true);
 std::array<U,8> topology{42|(U(5)<<32)};command(ob[1],topology,true);
 auto packet=[](unsigned kind,U serial,U occupancy,U history,U version){SummaryWord p{};p.w[0]=9;p.w[1]=42|(U(2)<<40)|(U(kind)<<48);p.w[2]=occupancy;p.w[3]=history;p.w[4]=version;p.w[5]=serial;return p;};
 std::array<SummaryWord,8> commands{};commands[0]=packet(3,16,5,7,11);commands[1].w[0]=1;commands[2]=packet(1,17,0,0,0);commands[3].w[0]=6;command(ob[0],commands);
 state_initialized=true;unsigned owner_calls=0,binding_calls=0,worker_calls=0;
 auto publish=[&](U cr,U cw,U rr,U rw,unsigned max_updates){auto run=owner(ob[0],ob[1],ob[2],ob[3],ob[4],ob[5],ob[6],ob[7],ob[8],1u,1u,0u,3u,U(9),4u,4u,4u,4u,cr,cw,rr,rw,U(0),U(0),4u,max_updates,8u,UINT64_MAX);run.wait();++owner_calls;auto done=read<SummaryWord>(ob[8]);require(done.w[6]==0,"publisher failed");std::cerr<<"XRT owner call="<<owner_calls<<" commands="<<done.w[3]<<" updates="<<done.w[4]<<" error="<<done.w[6]<<"\n";return done;};
 auto done=publish(0,2,0,0,0);require(done.w[0]==2&&done.w[1]==2,"publisher initialization counts");
 NativeSearchLabelSlot seed{3,5,0,1,2,UINT32_MAX,UINT32_MAX,0};command(seedbo,seed);
 auto search=[&](unsigned op,xrt::bo& parent){auto run=worker(labels,queue,journal,parent,observations,metadata,8u,8u,8u,42u,77u,U(9),0u,U(3),U(0),UINT64_MAX,1u,current,op);run.wait();++worker_calls;auto result=read<std::array<U,8>>(metadata);std::cerr<<"XRT worker call="<<worker_calls<<" op="<<op<<" queued="<<result[0]<<" observations="<<result[1]<<" status="<<result[2]<<"\n";return result;};
 auto state=search(4,seedbo);require(state[0]==1&&state[1]==0&&state[2]==0,"seed failed");
 state=search(2,seedbo);require(state[0]==0&&state[2]==0,"root frontier failed");
 xrt::bo reply_packet(ob[5],64,128),reply_receipt(ob[5],64,192),update_packet(ob[6],64,0),update_metadata(ob[6],64,64);
 auto bind=[&](xrt::bo& p,xrt::bo& envelope,U serial,unsigned op,U ticket,unsigned kind){auto run=binding(p,envelope,observations,status,42u,0u,2u,5u,serial,U(9),U(3),op,ticket,0u,0u,kind);run.wait();++binding_calls;auto result=read<std::uint32_t>(status);std::cerr<<"XRT binding call="<<binding_calls<<" kind="<<kind<<" status="<<result<<"\n";return result;};
 require(bind(reply_packet,reply_receipt,17,6,1,1)==0,"subscribe binding failed");state=search(1,current);require(state[0]==1&&state[1]==1&&state[2]==0,"first relaxation failed");
 auto retained=read<std::array<U,8>>(observations);require(bind(reply_packet,reply_receipt,17,6,2,1)==1,"wrong ticket accepted");require(read<std::array<U,8>>(observations)==retained,"binding rejection changed observation");
 commands[4]=packet(3,18,2,8,12);commands[5].w[0]=1;commands[5].w[2]=11;command(ob[0],commands);
 done=publish(2,3,2,2,4);require(done.w[0]==3&&done.w[1]==3&&done.w[2]==1,"publisher update counts");
 require(bind(update_packet,update_metadata,1,0,0,2)==0,"update binding failed");state=search(1,current);require(state[0]==2&&state[1]==2&&state[2]==0,"second relaxation failed");
 state=search(2,seedbo);auto best=read<NativeSearchLabelSlot>(current);require(state[0]==1&&state[2]==0&&best.node==42&&best.cost==20&&best.hops==3&&best.version==3,"updated frontier failed");
 state=search(2,seedbo);require(state[0]==0&&state[2]==1,"stale queue entry not discarded");auto preserved=read<NativeSearchLabelSlot>(current);require(std::memcmp(&best,&preserved,sizeof(best))==0,"stale pop changed output");
 seed.node=42;command(seedbo,seed);state=search(3,seedbo);auto traced=read<NativeSearchLabelSlot>(current);require(state[2]==0&&traced.cost==20&&traced.parent==1&&traced.edge==77&&traced.version==3,"trace failed");
 auto entries=read<std::array<NativeSearchResourceObservation,8>>(journal);require(entries[0].version==11&&entries[0].occupancy==5&&entries[0].history==7&&entries[1].version==12&&entries[1].occupancy==2&&entries[1].history==8,"journal values differ");
 auto actual_owner=read<SummaryWord>(ob[2]);require(actual_owner.w[1]==2&&actual_owner.w[2]==8&&actual_owner.w[3]==12,"owner state differs");
 std::cout<<"{\"status\":\"passed\",\"owner_calls\":"<<owner_calls<<",\"binding_calls\":"<<binding_calls<<",\"worker_calls\":"<<worker_calls<<",\"initialized_bos\":"<<initialized<<",\"authority_reuploads_after_initialization\":"<<authority_reuploads<<",\"final_cost\":20,\"observations\":2,\"scope\":\"Serialized three-CU fixture with direct shared BOs; not native routing, asynchronous search or board proof\"}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
