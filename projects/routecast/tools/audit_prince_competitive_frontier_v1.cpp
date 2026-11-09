// Independent raw branch predicates and ledger/connection/commit joins.
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <stdexcept>
#include <cmath>
#include <string>
using U=uint64_t;using Row=std::array<U,18>;
void require(bool b,const char* s){if(!b)throw std::runtime_error(s);}
U word(std::ifstream& f){U x;f.read((char*)&x,8);require(bool(f),"truncated ledger");return x;}
float number(U w){require(w<=0xffffffffULL,"float word upper bits");uint32_t a=w;float x;memcpy(&x,&a,4);return x;}
struct Entry{U phase,net,pin,sink,epoch;std::unordered_set<U> owned;};
int main(int argc,char** argv){try{
 require(argc==3,"directory cutoff required");std::string d=argv[1];U cutoff=std::stoull(argv[2]);std::unordered_map<U,std::array<U,4>> ends;
 {std::ifstream f(d+"/frontier.bin.connection_ends.bin",std::ios::binary);std::array<U,4> a;while(f.read((char*)a.data(),32)){require(a[0]<=cutoff,"future connection end");require(ends.emplace(a[2],a).second,"duplicate close");}require(f.eof()&&f.gcount()==0,"close file tail");}
 std::unordered_map<U,Entry> entries;std::unordered_map<U,std::unordered_map<U,uint8_t>> committed;U updates=0,matched=0,unattributed=0,epoch=0,phase=1,last=0;
 {std::ifstream f(d+"/queries.tsv.ledger.bin",std::ios::binary);require(bool(f),"ledger open");while(f.peek()!=EOF){U tag=word(f),e=word(f);
  if(tag==1||tag==4){require(e==epoch+1,"update epoch");epoch=e;U net=word(f),sign=word(f),n=word(f);require(sign<=1,"update sign");bool match=false;
   if(phase<=cutoff&&tag==1&&sign){++updates;auto end=ends.find(last);match=end!=ends.end()&&end->second[0]==phase&&end->second[1]==net&&end->second[3]+1==epoch;if(match)++matched;else ++unattributed;}
   for(U j=0;j<n;++j){U node=word(f);if(match)committed[last].emplace(node,0);}last=0;
  }else if(tag==2){require(e==epoch,"entry epoch");U id=word(f),net=word(f),pin=word(f),sink=word(f),n=word(f);last=id;
   if(phase<=cutoff){Entry a{phase,net,pin,sink,e,{}};for(U j=0;j<n;++j)require(a.owned.insert(word(f)).second,"duplicate entry owner");require(entries.emplace(id,std::move(a)).second,"duplicate entry");}
   else f.seekg(n*8,std::ios::cur);
  }else if(tag==3){require(e==epoch&&word(f)==phase,"phase epoch");++phase;last=0;
  }else if(tag==5){require(e==epoch,"terminal epoch");U n=word(f);for(U j=0;j<n;++j){word(f);U count=word(f);f.seekg(count*8,std::ios::cur);}require(f.peek()==EOF,"terminal tail");
  }else require(false,"unknown ledger tag");}}
 require(ends.size()==entries.size(),"prefix end/entry count");for(const auto& kv:entries){auto en=ends.at(kv.first);const auto& a=kv.second;require(en[0]==a.phase&&en[1]==a.net&&en[3]==a.epoch,"entry close context/epoch");}
 U connections=0;{std::ifstream f(d+"/queries.tsv.connections.tsv");U i,id,net,pin,sink,n;while(f>>i>>id>>net>>pin>>sink>>n){if(i>cutoff)continue;auto it=entries.find(id);require(it!=entries.end(),"connection absent from ledger");auto& a=it->second;require(i==a.phase&&net==a.net&&pin==a.pin&&sink==a.sink,"connection table join");require(n>=a.owned.size(),"tree count");++connections;}}require(connections==entries.size(),"connection count");
 std::vector<uint32_t> kind;{std::ifstream f(d+"/boundary/iteration_1.bin",std::ios::binary);char magic[8];f.read(magic,8);require(std::string(magic,8)=="RCBND001"&&word(f)==1,"RR header");U n=word(f);kind.resize(n);for(U j=0;j<n;++j){U id=word(f);uint32_t k,occ,cap,acc;f.read((char*)&k,4);f.read((char*)&occ,4);f.read((char*)&cap,4);f.read((char*)&acc,4);require(id<n,"RR id");kind[id]=k;}}
 std::map<U,std::array<U,4>> counts;U sequence=0,nonfinite=0,target_mismatch=0,rcv_count=0;
 {std::ifstream f(d+"/frontier.bin",std::ios::binary);char magic[8];f.read(magic,8);require(std::string(magic,8)=="RCFRNT01","frontier header");std::vector<Row> block(16384);
  while(f){f.read((char*)block.data(),block.size()*sizeof(Row));auto bytes=f.gcount();require(bytes%sizeof(Row)==0,"event tail");for(U j=0;j<U(bytes/sizeof(Row));++j){const auto& a=block[j];U tag=a[0];require(tag>=1&&tag<=4&&a[1]<=cutoff&&a[1]>=1,"event tag/cutoff");require(a[17]==++sequence,"event sequence");require(a[6]<kind.size()&&a[7]<kind.size()&&kind[a[7]]==a[9]&&(a[9]==4||a[9]==5),"event RR domain");auto it=entries.find(a[3]);require(it!=entries.end(),"event connection missing");auto& e=it->second;require(a[1]==e.phase&&a[2]==e.net&&a[4]==e.pin&&a[5]==e.sink&&a[10]==e.epoch,"event epoch context");require(a[16]==U(e.owned.count(a[7]))&&a[15]<=1,"event retained ownership/RCV");float bb=number(a[11]),nb=number(a[12]),bt=number(a[13]),nt=number(a[14]);bool accepted;
   if(tag<=2)accepted=a[15]?(bt>nt):(bb>nb);else {accepted=bt==nt;require(a[6]==a[7]&&a[12]==0,"pop reserved field");}
   require(accepted==(tag==1||tag==3),"native branch predicate mismatch");++counts[a[1]][tag-1];nonfinite+=!std::isfinite(bb)||!std::isfinite(nb)||!std::isfinite(bt)||!std::isfinite(nt);target_mismatch+=a[8]!=a[5];rcv_count+=a[15];auto ci=committed.find(a[3]);if(ci!=committed.end()){auto ni=ci->second.find(a[7]);if(ni!=ci->second.end())ni->second|=uint8_t(1<<(tag-1));}
  }}require(f.eof(),"event read failure");}
 {std::ifstream f(d+"/frontier.bin.phases.tsv");U i,c1,c2,c3,c4,total,closed,running=0;while(f>>i>>c1>>c2>>c3>>c4>>total>>closed){std::array<U,4> a{c1,c2,c3,c4};require(a==counts[i],"phase event counters");running+=c1+c2+c3+c4;require(total==running&&closed==U(i>cutoff),"phase cumulative/cutoff");}require(running==sequence,"phase sequence total");}
 U commit_nodes=0,commit_pre=0,commit_pop=0;for(auto& kv:committed)for(auto& n:kv.second){++commit_nodes;commit_pre+=bool(n.second&1);commit_pop+=bool(n.second&4);}
 std::array<U,4> totals{};for(auto& kv:counts)for(int i=0;i<4;++i)totals[i]+=kv.second[i];
 std::cout<<"{\"status\":\"BRANCH_CONTEXT_EPOCH_OWNERSHIP_CUTOFF_AND_COMMIT_JOIN_PASS\",\"events\":"<<sequence<<",\"prefix_connections\":"<<connections<<",\"tag_counts\":["<<totals[0]<<","<<totals[1]<<","<<totals[2]<<","<<totals[3]<<"],\"nonfinite_input_events\":"<<nonfinite<<",\"target_sink_mismatch_events\":"<<target_mismatch<<",\"RCV_events\":"<<rcv_count<<",\"positive_updates\":"<<updates<<",\"matched_post_connection_updates\":"<<matched<<",\"unattributed_updates\":"<<unattributed<<",\"committed_CHANNEL_nodes\":"<<commit_nodes<<",\"committed_with_preheap_accept\":"<<commit_pre<<",\"committed_with_valid_pop\":"<<commit_pop<<"}\n";
 return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
