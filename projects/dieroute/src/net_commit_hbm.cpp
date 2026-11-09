#include "net_commit_hbm.hpp"
namespace dieroute {namespace {
constexpr std::uint64_t max64=UINT64_MAX;
constexpr std::uint32_t none32=UINT32_MAX;
enum Space : unsigned {resource_space=0,tree_space=1,net_space=2,control_space=3};
struct Engine {
 const std::uint64_t *policy,*offsets,*arcs,*reads,*paths;
 const SummaryWord *shadows,*branches;
 SummaryWord *resources,*trees,*nets,*control,*scratch;
 std::uint32_t node_count,dies,shard_capacity,net_capacity,tree_capacity,scratch_capacity;
 std::uint64_t arc_count,session;
 std::uint32_t used=0;
 std::uint64_t error=0;
 void fail(std::uint64_t e){if(!error)error=e;}
 SummaryWord load(unsigned space,std::uint64_t index,bool overlay=true){
  if(overlay)for(std::uint32_t j=0;j<used;++j)if(scratch[j*2].w[0]==space&&scratch[j*2].w[1]==index)return scratch[j*2+1];
  if(space==resource_space)return resources[index];
  if(space==tree_space)return trees[index];
  if(space==net_space)return nets[index];
  return *control;
 }
 void store(unsigned space,std::uint64_t index,const SummaryWord& value){
  if(error)return;
  for(std::uint32_t j=0;j<used;++j)if(scratch[j*2].w[0]==space&&scratch[j*2].w[1]==index){scratch[j*2+1]=value;return;}
  if(used==scratch_capacity){fail(commit_no_space);return;}
  SummaryWord key={};key.w[0]=space;key.w[1]=index;scratch[used*2]=key;scratch[used*2+1]=value;++used;
 }
 unsigned owner(std::uint32_t node){
  if(node>=node_count){fail(commit_bad_argument);return 0;}
  auto p=policy[node];auto mask=unsigned((p>>32)&255);
  if(p>>41||!mask||(mask>>dies)){fail(commit_bad_record);return 0;}
  unsigned d=0;while(!(mask&(1u<<d)))++d;return d;
 }
 bool allowed(std::uint32_t node,std::uint32_t net){
  if(node>=node_count)return false;
  auto p=policy[node];owner(node);return !error&&!(p&(UINT64_C(1)<<40))&&(std::uint32_t(p)==none32||std::uint32_t(p)==net);
 }
 std::uint64_t topology(std::uint32_t node){return node|(((policy[node]>>32)&255)<<32);}
 std::uint64_t locate(std::uint32_t node,bool overlay,SummaryWord& value){
  const auto die=owner(node);if(error)return max64;
  const auto hash=(node*UINT32_C(2654435761))&(shard_capacity-1);const auto base=std::uint64_t(die)*shard_capacity;
  for(std::uint32_t probe=0;probe<shard_capacity;++probe){
   const auto index=base+((hash+probe)&(shard_capacity-1));auto r=load(resource_space,index,overlay);
   if(r.w[0]!=session){value={};value.w[4]=topology(node);value.w[5]=max64;return index;}
   if(r.w[4]>>40||std::uint32_t(r.w[4])>=node_count||r.w[2]==max64||r.w[6]||r.w[7]||r.w[1]>tree_capacity||((r.w[1]==0)!=(r.w[5]==max64))){fail(commit_bad_record);return max64;}
   if(std::uint32_t(r.w[4])==node){
    if(r.w[4]!=topology(node)){fail(commit_bad_record);return max64;}value=r;return index;
   }
  }
  value={};value.w[4]=topology(node);value.w[5]=max64;return max64;
 }
 SummaryWord entry(std::uint64_t index){
  SummaryWord empty={};if(index>=tree_capacity){fail(commit_bad_record);return empty;}
  auto e=load(tree_space,index);
  if(e.w[0]!=session||e.w[1]>=node_count||e.w[2]>=net_capacity||e.w[3]>none32||e.w[4]>none32||e.w[5]>none32){fail(commit_bad_record);return empty;}
  return e;
 }
 std::uint64_t membership(const SummaryWord& r,std::uint32_t slot){
  auto cursor=r.w[5];std::uint64_t found=max64;
  for(std::uint64_t i=0;i<r.w[1]&&!error;++i){
   auto e=entry(cursor);if(error)break;
   if(e.w[1]!=std::uint32_t(r.w[4])){fail(commit_bad_record);break;}
   if(e.w[2]==slot){if(found!=max64)fail(commit_bad_record);found=cursor;}
   cursor=e.w[7];
  }
  if(cursor!=max64)fail(commit_bad_record);
  return found;
 }
 bool read_contains(std::uint32_t node,std::uint32_t count){
  std::uint32_t lo=0,hi=count;
  while(lo<hi){auto mid=lo+(hi-lo)/2;if(reads[std::uint64_t(mid)*2]<node)lo=mid+1;else hi=mid;}
  return lo<count&&reads[std::uint64_t(lo)*2]==node;
 }
 bool edge(std::uint32_t from,std::uint32_t to,std::uint32_t pip){
  auto begin=offsets[from],end=offsets[from+1];
  if(begin>end||end>arc_count){fail(commit_bad_record);return false;}
  auto lo=begin,hi=end;
  while(lo<hi){auto mid=lo+(hi-lo)/2;auto v=arcs[mid];auto n=std::uint32_t(v),p=std::uint32_t(v>>32);if(n<to||(n==to&&p<pip))lo=mid+1;else hi=mid;}
  return lo<end&&arcs[lo]==(to|(std::uint64_t(pip)<<32));
 }
 std::uint64_t allocate(SummaryWord& ctl){
  auto index=ctl.w[4];
  if(index!=max64){
   if(index>=ctl.w[3]){fail(commit_bad_record);return max64;}auto old=load(tree_space,index);
   if(old.w[0]||old.w[1]||old.w[2]||old.w[3]||old.w[4]||old.w[5]||old.w[6]||(old.w[7]!=max64&&old.w[7]>=ctl.w[3])){fail(commit_bad_record);return max64;}
   ctl.w[4]=old.w[7];
  }else{if(ctl.w[3]==tree_capacity){fail(commit_no_space);return max64;}index=ctl.w[3]++;}
  return index;
 }
 void release(std::uint64_t index,SummaryWord& ctl){SummaryWord free={};free.w[7]=ctl.w[4];store(tree_space,index,free);ctl.w[4]=index;}
 void insert(std::uint32_t node,std::uint32_t slot,std::uint32_t parent,std::uint32_t pip,std::uint32_t depth,SummaryWord& net,SummaryWord& ctl){
  SummaryWord r={};auto pos=locate(node,true,r);if(error)return;
  if(pos==max64){fail(commit_no_space);return;}
  if(r.w[3]==max64||net.w[4]==max64){fail(commit_overflow);return;}
  if(membership(r,slot)!=max64){fail(commit_bad_path);return;}if(error)return;
  auto index=allocate(ctl);if(error)return;
  SummaryWord e={};e.w[0]=session;e.w[1]=node;e.w[2]=slot;e.w[3]=parent;e.w[4]=pip;e.w[5]=depth;e.w[6]=net.w[3];e.w[7]=r.w[5];store(tree_space,index,e);
  r.w[0]=session;++r.w[1];++r.w[3];r.w[5]=index;store(resource_space,pos,r);net.w[3]=index;++net.w[4];
 }
 void publish(){
  for(std::uint32_t i=0;i<used;++i){auto key=scratch[i*2];auto value=scratch[i*2+1];
   if(key.w[0]==resource_space)resources[key.w[1]]=value;
   else if(key.w[0]==tree_space)trees[key.w[1]]=value;
   else if(key.w[0]==net_space)nets[key.w[1]]=value;
   else *control=value;
  }
 }
};
bool zero(const SummaryWord& w,unsigned start){bool yes=true;for(unsigned i=start;i<8;++i)yes&=w.w[i]==0;return yes;}
bool power2(std::uint32_t n){return n&&!(n&(n-1));}
// Keep the completion AXI request in its own FSM. Otherwise HLS hoists it
// across the conditional delta loop and combines the request with its exit
// predicate, exceeding the clock budget even though the payload is registered.
void write_completion(SummaryWord* destination,const SummaryWord& value){
#ifdef __SYNTHESIS__
#pragma HLS INLINE off
#endif
 *destination=value;
}
}
extern "C" void dieroute_net_commit_hbm(
 const SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* reads,const SummaryWord* shadows,const SummaryWord* branches,const std::uint64_t* paths,
 SummaryWord* resources,SummaryWord* trees,SummaryWord* nets,SummaryWord* control,SummaryWord* scratch,
 SummaryWord* deltas,SummaryWord* completion,
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity,
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity,
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=command offset=slave bundle=traffic depth=2
#pragma HLS INTERFACE m_axi port=reads offset=slave bundle=traffic depth=64
#pragma HLS INTERFACE m_axi port=shadows offset=slave bundle=traffic depth=16
#pragma HLS INTERFACE m_axi port=branches offset=slave bundle=traffic depth=16
#pragma HLS INTERFACE m_axi port=paths offset=slave bundle=traffic depth=64
#pragma HLS INTERFACE m_axi port=scratch offset=slave bundle=traffic depth=256
#pragma HLS INTERFACE m_axi port=deltas offset=slave bundle=traffic depth=32
#pragma HLS INTERFACE m_axi port=completion offset=slave bundle=traffic depth=1
#pragma HLS INTERFACE m_axi port=policy offset=slave bundle=graph depth=32
#pragma HLS INTERFACE m_axi port=offsets offset=slave bundle=graph depth=33
#pragma HLS INTERFACE m_axi port=arcs offset=slave bundle=graph depth=64
#pragma HLS INTERFACE m_axi port=resources offset=slave bundle=authority depth=64
#pragma HLS INTERFACE m_axi port=trees offset=slave bundle=authority depth=64
#pragma HLS INTERFACE m_axi port=nets offset=slave bundle=authority depth=8
#pragma HLS INTERFACE m_axi port=control offset=slave bundle=authority depth=1
#pragma HLS AGGREGATE variable=command compact=none
#pragma HLS AGGREGATE variable=shadows compact=none
#pragma HLS AGGREGATE variable=branches compact=none
#pragma HLS AGGREGATE variable=resources compact=none
#pragma HLS AGGREGATE variable=trees compact=none
#pragma HLS AGGREGATE variable=nets compact=none
#pragma HLS AGGREGATE variable=control compact=none
#pragma HLS AGGREGATE variable=scratch compact=none
#pragma HLS AGGREGATE variable=deltas compact=none
#pragma HLS AGGREGATE variable=completion compact=none
#pragma HLS INTERFACE s_axilite port=command bundle=control
#pragma HLS INTERFACE s_axilite port=policy bundle=control
#pragma HLS INTERFACE s_axilite port=offsets bundle=control
#pragma HLS INTERFACE s_axilite port=arcs bundle=control
#pragma HLS INTERFACE s_axilite port=reads bundle=control
#pragma HLS INTERFACE s_axilite port=shadows bundle=control
#pragma HLS INTERFACE s_axilite port=branches bundle=control
#pragma HLS INTERFACE s_axilite port=paths bundle=control
#pragma HLS INTERFACE s_axilite port=resources bundle=control
#pragma HLS INTERFACE s_axilite port=trees bundle=control
#pragma HLS INTERFACE s_axilite port=nets bundle=control
#pragma HLS INTERFACE s_axilite port=control bundle=control
#pragma HLS INTERFACE s_axilite port=scratch bundle=control
#pragma HLS INTERFACE s_axilite port=deltas bundle=control
#pragma HLS INTERFACE s_axilite port=completion bundle=control
#pragma HLS INTERFACE s_axilite port=node_count bundle=control
#pragma HLS INTERFACE s_axilite port=arc_count bundle=control
#pragma HLS INTERFACE s_axilite port=dies bundle=control
#pragma HLS INTERFACE s_axilite port=shard_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=net_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=tree_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=read_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=shadow_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=branch_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=path_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=scratch_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=delta_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
 SummaryWord done={};done.w[1]=control->w[1];
 const auto cmd=command[0],counts=command[1];const auto session=cmd.w[0],op=cmd.w[1];
 if(!node_count||node_count==none32||!dies||dies>8||!power2(shard_capacity)||!net_capacity||net_capacity==none32||!tree_capacity||(!scratch_capacity||scratch_capacity>UINT32_MAX/2)||counts.w[0]>read_capacity||counts.w[1]>shadow_capacity||counts.w[2]>branch_capacity||counts.w[3]>path_capacity||counts.w[5]>1||!zero(counts,6)||op<1||op>7){done.w[0]=commit_bad_argument;write_completion(completion,done);return;}
 Engine e{policy,offsets,arcs,reads,paths,shadows,branches,resources,trees,nets,control,scratch,node_count,dies,shard_capacity,net_capacity,tree_capacity,scratch_capacity,arc_count,session};
 auto ctl=*control;
 if(!session||(op==commit_initialize?session<=ctl.w[0]:session!=ctl.w[0]))e.fail(commit_bad_session);
 if(!e.error&&op==commit_initialize){
  if(cmd.w[2]!=ctl.w[1]||!zero(counts,0)||cmd.w[3]||cmd.w[4]||cmd.w[5]||cmd.w[6]!=1||cmd.w[7])e.fail(commit_bad_argument);
  else {ctl={};ctl.w[0]=session;ctl.w[2]=1;ctl.w[4]=max64;ctl.w[5]=node_count|(std::uint64_t(dies)<<32);ctl.w[6]=shard_capacity|(std::uint64_t(net_capacity)<<32);ctl.w[7]=tree_capacity;e.store(control_space,0,ctl);}
 }else if(!e.error){
  if(ctl.w[5]!=(node_count|(std::uint64_t(dies)<<32))||ctl.w[6]!=(shard_capacity|(std::uint64_t(net_capacity)<<32))||ctl.w[7]!=tree_capacity||ctl.w[3]>tree_capacity||(ctl.w[4]!=max64&&ctl.w[4]>=ctl.w[3]))e.fail(commit_bad_record);
  else if(cmd.w[2]!=ctl.w[1]||cmd.w[6]!=ctl.w[2])e.fail(commit_bad_epoch);
  else if(op!=commit_query&&op!=commit_validate&&ctl.w[1]==max64)e.fail(commit_overflow);
  SummaryWord net={};std::uint32_t slot=std::uint32_t(cmd.w[3]),net_id=std::uint32_t(cmd.w[4]);
  if(op!=commit_negotiate){
   if(cmd.w[3]>=net_capacity||cmd.w[4]>=none32)e.fail(commit_bad_argument);
   if(!e.error){net=e.load(net_space,slot);if(op==commit_start){if(net.w[0]==session)e.fail(commit_bad_argument);else {net={};net.w[0]=session;net.w[1]=net_id;net.w[2]=cmd.w[7];net.w[3]=max64;}}
    else if(net.w[0]!=session||net.w[1]!=net_id||net.w[2]>=node_count||!net.w[4]||net.w[4]>tree_capacity||!net.w[5]||!zero(net,6))e.fail(commit_bad_record);
   }
  }
  if((op==commit_proposal&&(cmd.w[7]||counts.w[4]))||(op==commit_validate&&(cmd.w[7]||counts.w[2]||counts.w[3]||counts.w[4]||counts.w[5])))e.fail(commit_bad_argument);
  const auto read_count=std::uint32_t(counts.w[0]);
  if(!e.error&&(op==commit_proposal||op==commit_validate)){
   done.w[5]=net.w[5]!=cmd.w[5];std::uint64_t previous=max64;
   for(std::uint32_t i=0;i<read_count&&!e.error;++i){auto node=reads[std::uint64_t(i)*2];if(node>=node_count||(i&&node<=previous)){e.fail(commit_bad_argument);break;}previous=node;SummaryWord r={};e.locate(std::uint32_t(node),false,r);++done.w[2];done.w[3]+=r.w[3]!=reads[std::uint64_t(i)*2+1];}
   for(std::uint32_t i=0;i<counts.w[1]&&!e.error;++i){auto s=shadows[i];
    if(s.w[0]>=node_count||s.w[1]>=dies||!zero(s,5)||!e.read_contains(std::uint32_t(s.w[0]),read_count)){e.fail(commit_bad_argument);break;}
    auto n=std::uint32_t(s.w[0]);auto owner=e.owner(n);if(owner==s.w[1]||!(((policy[n]>>32)&255)&(UINT64_C(1)<<s.w[1]))){e.fail(commit_bad_argument);break;}
    SummaryWord r={};e.locate(n,false,r);done.w[4]+=s.w[2]!=r.w[1]||s.w[3]!=r.w[2]||s.w[4]!=r.w[3];
   }
   if(done.w[3]||done.w[4]||done.w[5])e.fail(commit_conflict);
   if(!e.error&&counts.w[5])e.fail(commit_overflow);
  }
  if(!e.error&&op==commit_query){
   if(!zero(counts,0)||cmd.w[7]>=node_count||!delta_capacity)e.fail(commit_bad_argument);
   else{auto n=std::uint32_t(cmd.w[7]);SummaryWord r={};e.locate(n,false,r);auto member=e.membership(r,slot);
    if(!e.error){SummaryWord delta={};delta.w[0]=session;delta.w[1]=n|(std::uint64_t(e.owner(n))<<32);delta.w[2]=r.w[1];delta.w[3]=r.w[2];delta.w[4]=r.w[3];delta.w[5]=ctl.w[1];delta.w[6]=(policy[n]>>32)&255;delta.w[7]=member!=max64;deltas[0]=delta;done.w[7]=1;}
   }
  }else if(!e.error&&op==commit_start){
   if(!zero(counts,0)||cmd.w[5]||cmd.w[7]>=node_count||!e.allowed(std::uint32_t(cmd.w[7]),net_id))e.fail(commit_bad_argument);
   for(std::uint32_t other=0;other<net_capacity&&!e.error;++other){auto registered=e.load(net_space,other,false);if(registered.w[0]==session&&registered.w[1]==net_id)e.fail(commit_bad_argument);}
   if(!e.error){SummaryWord r={};e.locate(std::uint32_t(cmd.w[7]),true,r);if(r.w[1])e.fail(commit_bad_path);else{e.insert(std::uint32_t(cmd.w[7]),slot,none32,none32,0,net,ctl);net.w[5]=1;e.store(net_space,slot,net);}}
  }else if(!e.error&&op==commit_proposal){
   auto original_count=net.w[4];std::uint64_t cursor=0;
   for(std::uint32_t b=0;b<counts.w[2]&&!e.error;++b){auto branch=branches[b];
    if(branch.w[0]>=node_count||branch.w[1]>=node_count||branch.w[2]!=cursor||branch.w[3]>counts.w[3]-cursor||branch.w[4]>none32||!zero(branch,6)){e.fail(commit_bad_argument);break;}
    auto parent=std::uint32_t(branch.w[0]);SummaryWord r={};e.locate(parent,true,r);auto attachment=e.membership(r,slot);
    if(attachment==max64||!e.allowed(parent,net_id)){e.fail(commit_bad_path);break;}auto anchor=e.entry(attachment);auto depth=anchor.w[5];std::uint64_t cost=0;
    for(std::uint64_t i=0;i<branch.w[3]&&!e.error;++i){auto encoded=paths[(cursor+i)*2];auto n=std::uint32_t(encoded),pip=std::uint32_t(encoded>>32);
     if(paths[(cursor+i)*2+1]||!e.read_contains(n,read_count)||!e.allowed(n,net_id)||!e.edge(parent,n,pip)){e.fail(commit_bad_path);break;}
     SummaryWord value={};e.locate(n,true,value);if(e.membership(value,slot)!=max64){e.fail(commit_bad_path);break;}
     if(depth==none32||value.w[2]>=max64-1||(value.w[1]&&cmd.w[6]>(max64-2-value.w[2])/value.w[1])){e.fail(commit_overflow);break;}
     auto delta=1+value.w[2]+cmd.w[6]*value.w[1];if(delta>=max64-cost){e.fail(commit_overflow);break;}cost+=delta;++depth;
     e.insert(n,slot,parent,pip,std::uint32_t(depth),net,ctl);parent=n;
    }
    cursor+=branch.w[3];if(parent!=branch.w[1]||depth!=branch.w[4]||cost!=branch.w[5])e.fail(commit_bad_path);
   }
   if(cursor!=counts.w[3])e.fail(commit_bad_argument);
   if(net.w[4]!=original_count){if(net.w[5]==max64)e.fail(commit_overflow);else{++net.w[5];e.store(net_space,slot,net);}}
  }else if(!e.error&&op==commit_ripup){
   if(!zero(counts,0)||cmd.w[5]!=net.w[5]||cmd.w[7])e.fail(commit_bad_argument);
   auto cursor=net.w[3];std::uint64_t root=max64;
   for(std::uint64_t i=0;i<net.w[4]&&!e.error;++i){auto entry=e.entry(cursor);if(e.error)break;auto next=entry.w[6];
    if(entry.w[2]!=slot){e.fail(commit_bad_record);break;}
    if(entry.w[1]==net.w[2]){if(root!=max64||entry.w[3]!=none32||entry.w[4]!=none32||entry.w[5]){e.fail(commit_bad_record);break;}root=cursor;}
    else {auto node=std::uint32_t(entry.w[1]);SummaryWord r={};auto pos=e.locate(node,true,r);
     if(e.membership(r,slot)!=cursor||!r.w[1]){e.fail(commit_bad_record);break;}if(r.w[3]==max64){e.fail(commit_overflow);break;}
     auto item=r.w[5];std::uint64_t predecessor=max64;
     for(std::uint64_t j=0;j<r.w[1]&&item!=cursor&&!e.error;++j){auto old=e.entry(item);predecessor=item;item=old.w[7];}
     if(item!=cursor){e.fail(commit_bad_record);break;}
     if(predecessor==max64)r.w[5]=entry.w[7];else{auto old=e.entry(predecessor);old.w[7]=entry.w[7];e.store(tree_space,predecessor,old);}
     --r.w[1];++r.w[3];e.store(resource_space,pos,r);e.release(cursor,ctl);
    }
    cursor=next;
   }
   if(cursor!=max64||root==max64)e.fail(commit_bad_record);
   if(!e.error&&net.w[4]>1){if(net.w[5]==max64)e.fail(commit_overflow);else{auto r=e.entry(root);r.w[6]=max64;e.store(tree_space,root,r);net.w[3]=root;net.w[4]=1;++net.w[5];e.store(net_space,slot,net);}}
  }else if(!e.error&&op==commit_negotiate){
   if(counts.w[0]||counts.w[1]||counts.w[2]||counts.w[3]||counts.w[5]||!counts.w[4]||cmd.w[3]||cmd.w[4]||cmd.w[5])e.fail(commit_bad_argument);
   for(std::uint64_t i=0;i<std::uint64_t(dies)*shard_capacity&&!e.error;++i){auto r=e.load(resource_space,i,false);if(r.w[0]!=session)continue;
    auto node=std::uint32_t(r.w[4]);SummaryWord checked={};auto pos=e.locate(node,false,checked);if(pos!=i){e.fail(commit_bad_record);break;}
    if(r.w[1]>1&&cmd.w[7]){auto excess=r.w[1]-1;if(r.w[3]==max64||cmd.w[7]>(max64-1-r.w[2])/excess){e.fail(commit_overflow);break;}r.w[2]+=cmd.w[7]*excess;++r.w[3];e.store(resource_space,i,r);}
   }
   ctl.w[2]=counts.w[4];
  }
  if(!e.error&&op!=commit_query&&op!=commit_validate){++ctl.w[1];e.store(control_space,0,ctl);}
 }
 std::uint32_t changes=0;
 for(std::uint32_t i=0;i<e.used;++i)if(scratch[i*2].w[0]==resource_space)++changes;
 if(!e.error&&changes>delta_capacity)e.fail(commit_no_space);
 if(!e.error){
  e.publish();done.w[1]=ctl.w[1];
  if(op!=commit_query){std::uint32_t emitted=0;for(std::uint32_t i=0;i<e.used;++i)if(scratch[i*2].w[0]==resource_space){auto r=scratch[i*2+1];auto node=std::uint32_t(r.w[4]);SummaryWord delta={};delta.w[0]=session;delta.w[1]=node|((scratch[i*2].w[1]/shard_capacity)<<32);delta.w[2]=r.w[1];delta.w[3]=r.w[2];delta.w[4]=r.w[3];delta.w[5]=ctl.w[1];delta.w[6]=r.w[4]>>32;deltas[emitted++]=delta;}done.w[7]=emitted;}
 }
 done.w[0]=e.error;done.w[6]=e.used;write_completion(completion,done);
}
}
