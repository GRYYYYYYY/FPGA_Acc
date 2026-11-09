#include "native_csr_io.hpp"
#include "summary_hbm.hpp"
#include <iostream>
#include <set>
#include <vector>
using namespace dieroute;
using namespace dieroute::native;
using U=std::uint64_t;
struct Frame {
 U h[16],cfg[8],cmd[16],ctl[8];
 const unsigned char *branches,*resources,*trees,*nets;
};
Frame read_frame(const Container& c,U pos){
 check(pos<=c.count&&c.count-pos>=56,"short frame");Frame f{};
 auto p=c.data+pos*8;
 for(unsigned i=0;i<16;++i)f.h[i]=le64(p+i*8);
 check(f.h[7]>=56&&f.h[7]<=c.count-pos,"frame length");
 for(unsigned i=0;i<8;++i){f.cfg[i]=le64(p+(16+i)*8);f.ctl[i]=le64(p+(48+i)*8);}
 for(unsigned i=0;i<16;++i)f.cmd[i]=le64(p+(24+i)*8);
 U cursor=56;
 auto take=[&](U count,U width){check(count<=(f.h[7]-cursor)/width,"frame section bounds");auto q=p+cursor*8;cursor+=count*width;return q;};
 take(f.h[8],2);take(f.h[9],8);f.branches=take(f.h[10],8);take(f.h[11],2);take(f.h[12],8);
 f.resources=take(f.h[13],9);f.trees=take(f.h[14],9);f.nets=take(f.h[15],9);
 check(cursor==f.h[7]&&f.cmd[1]==f.h[6],"frame structure");return f;
}
std::vector<SummaryWord> rows(const unsigned char* p,U count,U capacity){
 check(capacity<=SIZE_MAX/sizeof(SummaryWord),"allocation overflow");
 std::vector<SummaryWord> out(capacity);U previous=UINT64_MAX;
 for(U i=0;i<count;++i){auto r=p+i*72;U index=le64(r);check(index<capacity&&(i==0||index>previous),"indexed row order");previous=index;
  for(unsigned j=0;j<8;++j)out[index].w[j]=le64(r+(j+1)*8);
 }return out;
}
void save(const fs::path& p,const void* data,size_t n){std::ofstream out(p,std::ios::binary);out.write(static_cast<const char*>(data),n);check(bool(out),"snapshot write");}
int main(int argc,char** argv){try{
 check(argc==4||argc==5||argc==7,"usage: export_native_search_snapshot FRAMES ARCH OUT [SEQUENCE [post SINK]]");
 const bool post=argc==7;check(!post||std::string(argv[5])=="post","post mode");
 const U selected=argc>=5?std::stoull(argv[4]):UINT64_MAX;
 Container c(argv[1],0x44520025,8,fingerprint(argv[2]));Frame prev{};bool have=false;U pos=0,sequence=0;
 while(pos<c.count){auto f=read_frame(c,pos);check(f.h[0]==sequence++,"sequence");
  if(f.h[6]==3&&(selected==UINT64_MAX||f.h[0]==selected)){
   if(post){prev=f;have=true;}
   check(have&&f.h[10]>0,"proposal has no prior snapshot/branch");
   check(std::memcmp(prev.cfg,f.cfg,sizeof(f.cfg))==0,"configuration changed");
   check(prev.ctl[0]==f.cmd[0]&&prev.ctl[1]==f.cmd[2]+(post?1:0),"pre-proposal revision");
   check(f.cfg[2]&&f.cfg[3]<=SIZE_MAX/f.cfg[2],"resource capacity");
   auto res=rows(prev.resources,prev.h[13],f.cfg[2]*f.cfg[3]);
   auto trees=rows(prev.trees,prev.h[14],f.cfg[5]);auto nets=rows(prev.nets,prev.h[15],f.cfg[4]);
   check(f.cmd[3]<nets.size(),"net slot");auto net=nets[f.cmd[3]];
   check(net.w[0]==f.cmd[0]&&net.w[1]==f.cmd[4]&&net.w[5]==f.cmd[5]+(post?1:0),"net identity/generation");
   std::vector<SummaryWord> seeds;std::set<U> indices,nodes;U index=net.w[3];
   for(U i=0;i<net.w[4];++i){check(index<prev.ctl[3]&&index<trees.size()&&indices.insert(index).second,"tree chain bounds/cycle");auto t=trees[index];
    check(t.w[0]==f.cmd[0]&&t.w[2]==f.cmd[3]&&t.w[1]<f.cfg[0]&&nodes.insert(t.w[1]).second,"tree member identity");
    check(t.w[5]<UINT32_MAX&&t.w[3]<=UINT32_MAX&&t.w[4]<=UINT32_MAX,"tree seed width");seeds.push_back(t);index=t.w[6];
   }
   check(index==UINT64_MAX&&!seeds.empty(),"tree chain length");
   bool root=false;for(auto t:seeds){if(t.w[1]==net.w[2]){check(t.w[3]==UINT32_MAX&&t.w[4]==UINT32_MAX&&t.w[5]==0,"root fields");root=true;}else{
    bool parent=false;for(auto p:seeds)if(p.w[1]==t.w[3]&&p.w[5]+1==t.w[5])parent=true;check(parent,"tree parent/depth");
   }}check(root,"missing root");
   U sink=post?std::stoull(argv[6]):le64(f.branches+8);check(sink<f.cfg[0],"sink range");fs::path out=argv[3];check(!fs::exists(out),"output exists");fs::create_directories(out);
   save(out/"resources.raw",res.data(),res.size()*64);save(out/"trees.raw",trees.data(),trees.size()*64);save(out/"nets.raw",nets.data(),nets.size()*64);save(out/"control.raw",prev.ctl,64);save(out/"tree_seeds.raw",seeds.data(),seeds.size()*64);
   std::ofstream j(out/"snapshot.json");j<<"{\n  \"post_proposal\": "<<(post?"true":"false")<<",\n";j<<"  \"status\": \"exported\",\n  \"selection\": \"selected chronological proposal, first branch, immediately preceding authority\",\n  \"container_crc64_verified\": true,\n  \"proposal_sequence\": "<<f.h[0]<<",\n  \"source_frame_sequence\": "<<prev.h[0]<<",\n  \"session\": "<<prev.ctl[0]<<",\n  \"revision\": "<<prev.ctl[1]<<",\n  \"net_slot\": "<<f.cmd[3]<<",\n  \"net_id\": "<<f.cmd[4]<<",\n  \"sink\": "<<sink<<",\n  \"seed_count\": "<<seeds.size()<<",\n  \"config\": [";
   for(unsigned i=0;i<8;++i)j<<(i?", ":"")<<f.cfg[i];j<<"],\n  \"format\": \"little-endian raw 8-u64 SummaryWord; tree seeds retain complete original tree rows\",\n  \"board_result\": false\n}\n";check(bool(j),"manifest write");std::cout<<"exported sequence "<<f.h[0]<<" seeds "<<seeds.size()<<" sink "<<sink<<"\n";return 0;
  }prev=f;have=true;pos+=f.h[7];
 }throw std::runtime_error("no proposal");
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
