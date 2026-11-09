// Independent attempt lifecycle, legacy sequence join and actual-BB audit.
#include <array>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#include <cstdint>
#include <cstring>
#include <cmath>
#include <stdexcept>
#include <string>
using U=uint64_t;using Meta=std::array<U,32>;using Event=std::array<U,18>;
void need(bool ok,const char*s){if(!ok)throw std::runtime_error(s);}
float f32(U bits){need(bits<=0xffffffffULL,"float upper bits");uint32_t b=bits;float v;std::memcpy(&v,&b,4);return v;}
struct Attempt{Meta begin{};U end=0;bool found=false;std::array<U,3> costs{};};
bool equal_context(const Meta&a,const Meta&b){for(int i=1;i<=8;++i)if(a[i]!=b[i])return false;for(int i=10;i<=27;++i)if(a[i]!=b[i])return false;return true;}
int main(int argc,char**argv){try{
 need(argc==4,"directory cutoff pointfile required");std::string d=argv[1];U cutoff=std::stoull(argv[2]);std::map<U,std::array<int64_t,3>>points;{std::ifstream f(argv[3]);U n;int64_t x,y,z;while(f>>n>>x>>y>>z)need(points.emplace(n,std::array<int64_t,3>{x,y,z}).second,"duplicate drive point");}need(!points.empty(),"empty points");
 std::map<U,std::array<U,4>>close;{std::ifstream f(d+"/frontier.bin.connection_ends.bin",std::ios::binary);std::array<U,4>a;while(f.read((char*)a.data(),32))need(close.emplace(a[2],a).second,"duplicate connection end");need(f.eof()&&f.gcount()==0,"connection tail");}
 std::map<U,std::array<U,4>>connections;{std::ifstream f(d+"/queries.tsv.connections.tsv");U phase,id,net,pin,sink,size;while(f>>phase>>id>>net>>pin>>sink>>size)if(phase<=cutoff)connections[id]={phase,net,pin,sink};}need(close.size()==connections.size(),"prefix connections");
 std::vector<Attempt>attempts;Attempt active;bool open=false;U serial=0,last_end=0,found_count=0,failed=0,unsupported=0,popped_stored_mismatch=0,stored_g_mismatch=0;std::map<U,U>ordinals;U rcv=0;
 {std::ifstream f(d+"/frontier.bin.attempts.bin",std::ios::binary);char h[8];f.read(h,8);need(std::string(h,8)=="RCATT001","attempt header");Meta a;
  while(f.read((char*)a.data(),256)){
   if(a[0]==9){++unsupported;continue;}
   need(a[0]>=1&&a[0]<=3&&a[1]>=1&&a[1]<=cutoff,"attempt tag/cutoff");need(a[31]<=1,"found flag domain");
   if(a[0]==1){need(!open,"nested attempt");need(a[6]==++serial&&a[7]==++ordinals[a[3]],"attempt ordinal");need(a[9]==last_end,"attempt watermark gap");auto ci=connections.find(a[3]);need(ci!=connections.end(),"attempt missing connection");need(ci->second==std::array<U,4>{a[1],a[2],a[4],a[5]},"attempt connection context");auto end=close.at(a[3]);need(end[0]==a[1]&&end[1]==a[2]&&end[3]==a[8],"attempt epoch");for(int i=10;i<22;i+=2)need(int64_t(a[i])<=int64_t(a[i+1]),"attempt box domain");for(int i=22;i<=26;++i)need(std::isfinite(f32(a[i])),"attempt parameter domain");need(f32(a[22])>=0&&f32(a[22])<=1&&a[27]<=1,"attempt parameter range");need(!a[31]&&!a[28]&&!a[29]&&!a[30],"begin cost sentinel");active=Attempt{};active.begin=a;open=true;rcv+=a[27];
   }else{need(open&&equal_context(active.begin,a),"attempt context changed");need(a[9]>=active.begin[9],"attempt backwards sequence");
    if(a[0]==2){need(!active.found&&a[31]==1,"duplicate/missing target");active.found=true;for(int i=0;i<3;++i){need(std::isfinite(f32(a[28+i])),"nonfinite successful target cost");active.costs[i]=a[28+i];}active.end=a[9];
    }else{need(a[31]==U(active.found),"attempt end found flag");if(active.found){for(int i=0;i<3;++i)need(a[28+i]==active.costs[i],"attempt outcome changed");need(a[9]==active.end,"CHANNEL events after target pop");++found_count;popped_stored_mismatch+=active.costs[0]!=active.costs[1];stored_g_mismatch+=active.costs[1]!=active.costs[2];}else{need(!a[28]&&!a[29]&&!a[30],"failed target sentinel");++failed;}active.end=a[9];last_end=a[9];attempts.push_back(std::move(active));open=false;}
   }
  }need(f.eof()&&f.gcount()==0&&!open,"truncated/unclosed attempt");}
 need(!attempts.empty()&&!unsupported,"unsupported search mode");U missing=0,retried=0;for(auto&kv:connections){if(!ordinals.count(kv.first))++missing;else retried+=ordinals[kv.first]>1;}
 U sequence=0,inside_checks=0,outside_owned=0;size_t ai=0;
 {std::ifstream f(d+"/frontier.bin",std::ios::binary);char h[8];f.read(h,8);need(std::string(h,8)=="RCFRNT01","frontier header");std::vector<Event>block(16384);
  while(f){f.read((char*)block.data(),block.size()*sizeof(Event));auto bytes=f.gcount();need(bytes%sizeof(Event)==0,"frontier tail");for(U j=0;j<U(bytes/sizeof(Event));++j){auto&e=block[j];need(e[17]==++sequence,"frontier sequence");while(ai<attempts.size()&&sequence>attempts[ai].end)++ai;need(ai<attempts.size(),"event beyond attempt");auto&a=attempts[ai].begin;need(sequence>a[9]&&sequence<=attempts[ai].end,"event outside attempt interval");need(e[1]==a[1]&&e[2]==a[2]&&e[3]==a[3]&&e[4]==a[4]&&e[5]==a[5]&&e[8]==a[5]&&e[10]==a[8]&&e[15]==a[27],"event attempt context");auto p=points.find(e[7]);need(p!=points.end(),"event drive point absent");bool inside=true;for(int k=0;k<3;++k)inside&=p->second[k]>=int64_t(a[10+2*k])&&p->second[k]<=int64_t(a[11+2*k]);if(!e[15]){if(e[0]<=2)need(inside,"preheap outside attempt BB");else if(!inside){need(e[16],"unowned pop outside attempt BB");++outside_owned;}++inside_checks;}
  }}need(f.eof(),"frontier read error");}need(sequence==last_end,"final attempt watermark");
 std::cout<<"{\"status\":\"ATTEMPT_LIFECYCLE_TARGET_BITS_AND_ALL_CHANNEL_INTERVALS_PASS\",\"attempts\":"<<attempts.size()<<",\"found\":"<<found_count<<",\"failed\":"<<failed<<",\"unsupported\":"<<unsupported<<",\"retried_connections\":"<<retried<<",\"connections_without_attempt\":"<<missing<<",\"events_joined\":"<<sequence<<",\"actual_BB_checks\":"<<inside_checks<<",\"outside_owned_pops\":"<<outside_owned<<",\"RCV_attempts\":"<<rcv<<",\"popped_vs_stored_target_f_mismatch\":"<<popped_stored_mismatch<<",\"stored_target_f_vs_g_mismatch\":"<<stored_g_mismatch<<"}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
