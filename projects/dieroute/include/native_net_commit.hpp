#pragma once
#include "native_csr_io.hpp"
#include "native_net_transaction.hpp"
#include "net_commit_hbm.hpp"
#include <functional>
namespace dieroute {
// CPU orchestration around the synthesizable whole-net authority. All mutable
// authority arrays are private and are written only by the kernel after their
// initial zero allocation. Exported NativeRouteState objects are search views.
class NativeNetCommit {
 using U=std::uint64_t;
 using N=std::uint32_t;
 NativeOwnerLayout layout_;
 std::vector<U> policy_;
 const U *offsets_,*arcs_;U arc_count_;
 N shard_capacity_,tree_capacity_,scratch_capacity_,delta_capacity_;
 std::map<N,N> slots_;
 std::vector<SummaryWord> resources_,trees_,nets_,scratch_,deltas_;
 SummaryWord control_{},completion_{};std::array<SummaryWord,2> command_{};
 std::vector<U> reads_,paths_;std::vector<SummaryWord> shadows_,branches_;
 std::map<N,SummaryWord> pending_;
 native::Writer frames_,publications_;
 std::array<U,5> context_{};U sequence_=0;
 bool initialized_publications_=false;
 static void require(bool ok,const char* why){if(!ok)throw std::logic_error(why);}
 static N capacity(U value){require(value>0&&value<UINT32_MAX,"native commit capacity range");return N(value);}
 static N power_capacity(U value){U n=16;while(n<value)n*=2;return capacity(n);}
 bool allowed(N n,N net)const{return n<policy_.size()&&!(policy_[n]&(U(1)<<40))&&(N(policy_[n])==UINT32_MAX||N(policy_[n])==net);}
 bool edge(N a,N b,N pip)const{
  U lo=offsets_[a],end=offsets_[a+1],hi=end;require(lo<=end&&end<=arc_count_,"commit snapshot CSR row");
  while(lo<hi){auto mid=lo+(hi-lo)/2;auto v=arcs_[mid];if(std::make_pair(N(v),N(v>>32))<std::make_pair(b,pip))lo=mid+1;else hi=mid;}
  return lo<end&&arcs_[lo]==(b|(U(pip)<<32));
 }
 const SummaryWord* resource(N node)const{
  auto base=U(layout_.owner(node))*shard_capacity_;auto hash=(node*UINT32_C(2654435761))&(shard_capacity_-1);
  for(N j=0;j<shard_capacity_;++j){const auto& r=resources_[base+((hash+j)&(shard_capacity_-1))];if(r.w[0]!=control_.w[0])return nullptr;if(N(r.w[4])==node)return &r;}
  return nullptr;
 }
 void request(U op,N net=UINT32_MAX){
  command_={};reads_.clear();paths_.clear();shadows_.clear();branches_.clear();
  auto& c=command_[0];c.w[0]=control_.w[0];c.w[1]=op;c.w[2]=control_.w[1];c.w[6]=control_.w[2];
  if(net!=UINT32_MAX){c.w[3]=slots_.at(net);c.w[4]=net;c.w[5]=nets_[c.w[3]].w[0]==control_.w[0]?nets_[c.w[3]].w[5]:0;}
 }
 void append(native::Writer& writer,const U* p,std::size_t words){if(words)writer.append(reinterpret_cast<const unsigned char*>(p),words*8);}
 void trace(){
  U nr=0,nn=0;for(const auto& r:resources_)nr+=r.w[0]==control_.w[0];for(const auto& n:nets_)nn+=n.w[0]==control_.w[0];
  const auto& z=command_[1];U header[16]={sequence_++,context_[0],context_[1],context_[2],context_[3],context_[4],command_[0].w[1],0,z.w[0],z.w[1],z.w[2],z.w[3],completion_.w[7],nr,control_.w[3],nn};
  header[7]=56+2*z.w[0]+8*z.w[1]+8*z.w[2]+2*z.w[3]+8*completion_.w[7]+9*(nr+control_.w[3]+nn);
  U config[8]={policy_.size(),arc_count_,layout_.count(),shard_capacity_,nets_.size(),tree_capacity_,scratch_capacity_,delta_capacity_};
  append(frames_,header,16);append(frames_,config,8);append(frames_,command_[0].w,16);append(frames_,completion_.w,8);append(frames_,control_.w,8);
  append(frames_,reads_.data(),z.w[0]*2);if(z.w[1])append(frames_,shadows_[0].w,z.w[1]*8);if(z.w[2])append(frames_,branches_[0].w,z.w[2]*8);append(frames_,paths_.data(),z.w[3]*2);if(completion_.w[7])append(frames_,deltas_[0].w,completion_.w[7]*8);
  auto records=[&](const auto& rows,U count,bool tagged){for(U i=0;i<count;++i)if(!tagged||rows[i].w[0]==control_.w[0]){append(frames_,&i,1);append(frames_,rows[i].w,8);}};
  records(resources_,resources_.size(),true);records(trees_,control_.w[3],false);records(nets_,nets_.size(),true);
 }
 void invoke(bool proposal=false){
  command_[1].w[0]=reads_.size()/2;command_[1].w[1]=shadows_.size();command_[1].w[2]=branches_.size();command_[1].w[3]=paths_.size()/2;
  // Keep non-null buffers even for zero-length payloads. Capacities describe
  // allocated elements, while descriptors alone define what is consumed.
  const auto rc=capacity(std::max<std::size_t>(1,reads_.size()/2)),sc=capacity(std::max<std::size_t>(1,shadows_.size())),bc=capacity(std::max<std::size_t>(1,branches_.size())),pc=capacity(std::max<std::size_t>(1,paths_.size()/2));
  reads_.resize(rc*U(2));shadows_.resize(sc);branches_.resize(bc);paths_.resize(pc*U(2));completion_={};
  dieroute_net_commit_hbm(command_.data(),policy_.data(),offsets_,arcs_,reads_.data(),shadows_.data(),branches_.data(),paths_.data(),resources_.data(),trees_.data(),nets_.data(),&control_,scratch_.data(),deltas_.data(),&completion_,capacity(policy_.size()),arc_count_,layout_.count(),shard_capacity_,capacity(nets_.size()),tree_capacity_,rc,sc,bc,pc,scratch_capacity_,delta_capacity_);
  require(completion_.w[7]<=delta_capacity_&&control_.w[3]<=tree_capacity_,"native commit output bounds");trace();
  if(completion_.w[0]!=commit_ok&&!(proposal&&completion_.w[0]==commit_conflict))throw std::runtime_error("native commit kernel rejected op "+std::to_string(command_[0].w[1])+" status "+std::to_string(completion_.w[0]));
  if(completion_.w[0]==commit_ok)for(U i=0;i<completion_.w[7];++i){const auto& d=deltas_[i];require(d.w[0]==control_.w[0]&&N(d.w[1])<policy_.size()&&d.w[5]==control_.w[1]&&!d.w[7],"native commit delta identity");auto n=N(d.w[1]);require(d.w[1]==(n|(U(layout_.owner(n))<<32))&&d.w[6]==layout_.membership(n),"native commit delta topology");auto r=resource(n);require(r&&r->w[1]==d.w[2]&&r->w[2]==d.w[3]&&r->w[3]==d.w[4],"native commit delta not authoritative");if(d.w[6]&(d.w[6]-1))pending_[n]=d;}
 }
public:
 NativeNetCommit(NativeOwnerLayout layout,std::vector<U> policy,const U* offsets,const U* arcs,U arc_count,const std::vector<N>& order,const native::fs::path& out,native::Fingerprint arch)
  :layout_(std::move(layout)),policy_(std::move(policy)),offsets_(offsets),arcs_(arcs),arc_count_(arc_count),
   shard_capacity_(power_capacity(std::min<U>(policy_.size(),std::max<U>(16,order.size()*2048)))),
   tree_capacity_(capacity(std::max<U>(64,std::min<U>(U(policy_.size())*order.size(),order.size()*2048)))),
   scratch_capacity_(capacity(std::max<U>(128,std::min<U>(tree_capacity_*U(3)+2,U(policy_.size())*order.size()*3+order.size()+1)))),
   delta_capacity_(capacity(std::max<U>(32,std::min<U>(policy_.size(),U(layout_.count())*shard_capacity_)))),
   resources_(U(layout_.count())*shard_capacity_),trees_(tree_capacity_),nets_(order.size()),scratch_(U(scratch_capacity_)*2),deltas_(delta_capacity_),
   frames_(out/"net_commit_frames.bin",0x44520025,0,arch),publications_(out/"net_commit_publications.bin",0x44520027,0,arch){
  const std::uint16_t endian=1;require(*reinterpret_cast<const unsigned char*>(&endian)==1,"native commit requires little endian mapped CSR");require(!order.empty()&&policy_.size()<UINT32_MAX&&offsets_[0]==0&&offsets_[policy_.size()]==arc_count_,"native commit graph shape");
  for(N i=0;i<order.size();++i)require(slots_.emplace(order[i],i).second,"duplicate native commit net");
  for(N n=0;n<policy_.size();++n)require(!(policy_[n]>>41)&&((policy_[n]>>32)&255)==layout_.membership(n),"native commit policy membership");
  native::Writer writer(out/"net_commit_policy.bin",0x44520026,policy_.size(),arch);writer.append(reinterpret_cast<const unsigned char*>(policy_.data()),policy_.size()*8);writer.finish(8);
 }
 void context(U rep,U epoch,U wave,U actor,U attempt){context_={rep,epoch,wave,actor,attempt};}
 void initialize(U session){request(commit_initialize);command_[0].w[0]=session;command_[0].w[6]=1;invoke();pending_.clear();initialized_publications_=false;}
 void start(N net,N root){request(commit_start,net);command_[0].w[7]=root;invoke();}
 void ripup(N net){request(commit_ripup,net);invoke();}
 void negotiate(U increment,U next_present){request(commit_negotiate);command_[0].w[7]=increment;command_[1].w[4]=next_present;invoke();}
 U generation(N net)const{return nets_.at(slots_.at(net)).w[5];}
 U present()const{return control_.w[2];}
 const SummaryWord& completion()const{return completion_;}
 bool commit(const NativeNetProposal& p,U generation){
  request(commit_proposal,p.net);command_[0].w[5]=generation;command_[0].w[6]=p.present;command_[1].w[5]=p.overflow;
  for(auto n:p.reads){reads_.push_back(n);auto r=p.snapshot->find_use(n);reads_.push_back(r?r->version:0);}
  for(const auto& r:p.shadow_reads){SummaryWord w={};w.w[0]=r.node;w.w[1]=r.worker;w.w[2]=r.seen.occupancy;w.w[3]=r.seen.history;w.w[4]=r.seen.version;shadows_.push_back(w);}
  for(const auto& b:p.branches)if(b.result.status==SparseSearchStatus::found){SummaryWord w={};w.w[0]=b.result.attachment;w.w[1]=b.task.sink;w.w[2]=paths_.size()/2;w.w[3]=b.result.path.size();w.w[4]=b.result.hops;w.w[5]=b.result.cost;branches_.push_back(w);require(b.result.path.size()==b.result.edges.size(),"native commit proposal shape");for(U i=0;i<b.result.path.size();++i){paths_.push_back(b.result.path[i]|(U(b.result.edges[i])<<32));paths_.push_back(0);}}
  invoke(true);return completion_.w[0]==commit_ok;
 }
 NativeRouteState snapshot()const{
  const auto session=control_.w[0];require(session&&control_.w[3]<=tree_capacity_,"native commit snapshot control");
  std::map<N,NativeTree> trees;std::map<N,NativeUse> uses;std::set<U> live,free;
  for(N slot=0;slot<nets_.size();++slot){const auto& net=nets_[slot];if(net.w[0]!=session)continue;require(net.w[1]<UINT32_MAX&&net.w[2]<policy_.size()&&net.w[4]&&net.w[4]<=tree_capacity_&&net.w[5]&&!net.w[6]&&!net.w[7],"native commit net record");require(slots_.at(N(net.w[1]))==slot,"native commit net-slot binding");NativeTree t;t.source=N(net.w[2]);auto next=net.w[3];for(U j=0;j<net.w[4];++j){require(next<control_.w[3]&&live.insert(next).second,"native commit tree pool alias");const auto& e=trees_[next];require(e.w[0]==session&&e.w[1]<policy_.size()&&e.w[2]==slot&&e.w[3]<=UINT32_MAX&&e.w[4]<=UINT32_MAX&&e.w[5]<=UINT32_MAX,"native commit tree record");require(t.nodes.emplace(N(e.w[1]),NativeTreeNode{N(e.w[3]),N(e.w[4]),N(e.w[5])}).second,"duplicate native commit tree node");next=e.w[6];}require(next==UINT64_MAX,"native commit tree tail");require(trees.emplace(N(net.w[1]),std::move(t)).second,"native commit net identity");}
  for(U i=0;i<resources_.size();++i){const auto& r=resources_[i];if(r.w[0]!=session)continue;auto n=N(r.w[4]);require(n<policy_.size()&&r.w[4]==(n|(U(layout_.membership(n))<<32))&&i/shard_capacity_==layout_.owner(n)&&resource(n)==&r&&r.w[2]<UINT64_MAX&&r.w[3]&&!r.w[6]&&!r.w[7],"native commit resource record");NativeUse u;u.history=r.w[2];u.version=r.w[3];auto next=r.w[5];require(r.w[1]<=live.size(),"native commit occupancy bounds");for(U j=0;j<r.w[1];++j){require(live.count(next),"native commit membership outside live pool");const auto& e=trees_[next];require(e.w[1]==n&&u.nets.insert(N(nets_[e.w[2]].w[1])).second,"native commit resource membership alias");next=e.w[7];}require(next==UINT64_MAX&&uses.emplace(n,std::move(u)).second,"native commit resource tail/identity");}
  auto next=control_.w[4];while(next!=UINT64_MAX){require(next<control_.w[3]&&!live.count(next)&&free.insert(next).second,"native commit free chain alias");const auto& e=trees_[next];for(unsigned j=0;j<7;++j)require(!e.w[j],"native commit nonzero free record");next=e.w[7];}require(live.size()+free.size()==control_.w[3],"native commit lost allocated tree entry");
  return NativeRouteState::checkpoint(std::move(trees),std::move(uses),[&](N n,N net){return allowed(n,net);},[&](N a,N b,N pip){return edge(a,b,pip);},layout_);
 }
 std::vector<SummaryWord> publications(const std::vector<U>& topology){
  const bool initial=!initialized_publications_;std::vector<SummaryWord> result;
  if(initial){for(auto t:topology){N n=N(t);require((t>>32)==layout_.membership(n),"native commit publication directory");auto r=resource(n);SummaryWord d={};d.w[0]=control_.w[0];d.w[1]=n|(U(layout_.owner(n))<<32);if(r){d.w[2]=r->w[1];d.w[3]=r->w[2];d.w[4]=r->w[3];}d.w[5]=control_.w[1];d.w[6]=t>>32;result.push_back(d);}}
  else for(const auto& item:pending_)result.push_back(item.second);
  for(const auto& d:result){U prefix[8]={context_[0],context_[1],context_[2],context_[3],context_[4],U(initial),sequence_,0};append(publications_,prefix,8);append(publications_,d.w,8);}
  initialized_publications_=true;pending_.clear();return result;
 }
 static void compare(const NativeRouteState& actual,const NativeRouteState& oracle){
  require(actual.layout().same(oracle.layout())&&actual.trees().size()==oracle.trees().size()&&actual.use_count()==oracle.use_count(),"native commit oracle shape");
  for(const auto& item:oracle.trees())require(native_same_tree(actual.tree(item.first),item.second),"native commit oracle tree mismatch");
  oracle.visit_uses([&](auto n,const auto& u){require(native_same_use(actual.find_use(n),&u),"native commit oracle resource mismatch");});
 }
 void finish(){frames_.finish_dynamic(8);publications_.finish_dynamic(128);}
};
}
