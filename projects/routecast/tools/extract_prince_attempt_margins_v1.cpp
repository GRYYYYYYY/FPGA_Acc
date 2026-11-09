// Exact ordering of float32 ratios via 48-bit mantissa products and exponent alignment.
#include <array>
#include <map>
#include <vector>
#include <fstream>
#include <iostream>
#include <cstdint>
#include <cmath>
#include <cstring>
#include <stdexcept>
using U=uint64_t;using Meta=std::array<U,32>;using Event=std::array<U,18>;
void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
float val(U w){uint32_t a=w;need(w==a,"word");float f;memcpy(&f,&a,4);return f;}
struct Dyad{int sign,exp;U mant;};
Dyad dyad(U w){U field=(w>>23)&255,m=w&0x7fffff;need(field!=255,"nonfinite dyad");if(field)m|=1<<23;return {m?((w>>31)?-1:1):0,field?int(field)-150:-149,m};}
int positive_compare(U a,int ae,U b,int be){if(!a||!b)return (a>0)-(b>0);int al=64-__builtin_clzll(a),bl=64-__builtin_clzll(b);if(al+ae!=bl+be)return al+ae>bl+be?1:-1;if(ae>be)a<<=ae-be;else b<<=be-ae;return(a>b)-(a<b);}
bool less_ratio(U f1,U s1,U f2,U s2){auto a=dyad(f1),b=dyad(s1),c=dyad(f2),d=dyad(s2);need(b.sign==1&&d.sign==1,"positive denominator");if(a.sign!=c.sign)return a.sign<c.sign;if(!a.sign)return false;int cmp=positive_compare(a.mant*d.mant,a.exp+d.exp,c.mant*b.mant,c.exp+b.exp);return a.sign>0?cmp<0:cmp>0;}
struct Attempt{Meta b{};U end=0,sink=0;bool found=false;};
struct Aggregate{U count=0,normal=0,zero=0,invalid=0,nonfinite=0,f=0,sink=0,sequence=0,attempt=0;};
void add(Aggregate&a,const Event&e,const Attempt&t){++a.count;float sink=val(t.sink),f=val(e[14]);if(!t.found||!std::isfinite(sink)||sink<0){++a.invalid;return;}if(sink==0){++a.zero;return;}if(!std::isfinite(f)){++a.nonfinite;return;}++a.normal;if(a.normal==1||less_ratio(e[14],t.sink,a.f,a.sink)){a.f=e[14];a.sink=t.sink;a.sequence=e[17];a.attempt=t.b[6];}}
int main(int argc,char**argv){try{need(argc==4,"directory cutoff output");std::string dir=argv[1];U cut=std::stoull(argv[2]);std::vector<Attempt>attempts;Attempt a;bool open=false;{std::ifstream in(dir+"/frontier.bin.attempts.bin",std::ios::binary);char h[8];in.read(h,8);need(std::string(h,8)=="RCATT001","metadata header");Meta r;while(in.read((char*)r.data(),256)){need(r[1]<=cut,"future metadata");if(r[0]==1){need(!open,"nested");a=Attempt{};a.b=r;open=true;}else if(r[0]==2){need(open&&r[6]==a.b[6],"found context");a.sink=r[28];a.found=true;}else if(r[0]==3){need(open&&r[6]==a.b[6],"end context");a.end=r[9];attempts.push_back(a);open=false;}else need(false,"unsupported mode");}need(in.eof()&&in.gcount()==0&&!open,"metadata tail");}
std::map<std::pair<U,U>,std::array<Aggregate,2>> result;size_t index=0;U count=0;{std::ifstream in(dir+"/frontier.bin",std::ios::binary);char h[8];in.read(h,8);need(std::string(h,8)=="RCFRNT01","frontier header");std::vector<Event>block(16384);while(in){in.read((char*)block.data(),block.size()*sizeof(Event));auto n=in.gcount();need(n%sizeof(Event)==0,"event tail");for(U j=0;j<U(n/sizeof(Event));++j){const auto&e=block[j];need(e[1]<=cut,"future event");if(e[0]!=1)continue;while(index<attempts.size()&&e[17]>attempts[index].end)++index;need(index<attempts.size(),"interval absent");const auto&t=attempts[index];need(e[17]>t.b[9]&&e[3]==t.b[3]&&e[1]==t.b[1]&&e[2]==t.b[2]&&e[8]==t.b[5]&&e[10]==t.b[8],"attempt join");auto&r=result[{e[2],e[7]}];add(r[0],e,t);if(e[1]==cut)add(r[1],e,t);++count;}}need(in.eof(),"event read");}
std::ofstream out(argv[3]);need(bool(out),"output");U rows=0;for(auto&kv:result)for(int horizon=0;horizon<2;++horizon){auto&a=kv.second[horizon];if(!a.count)continue;out<<"{\"net\":"<<kv.first.first<<",\"node\":"<<kv.first.second<<",\"horizon\":\""<<(horizon?"ready":"prefix")<<"\",\"accepted_events\":"<<a.count<<",\"normalizable_events\":"<<a.normal<<",\"zero_target_events\":"<<a.zero<<",\"invalid_target_events\":"<<a.invalid<<",\"nonfinite_candidate_events\":"<<a.nonfinite<<",\"min_f_bits\":";if(a.normal)out<<a.f;else out<<"null";out<<",\"min_sink_f_bits\":";if(a.normal)out<<a.sink;else out<<"null";out<<",\"min_event\":";if(a.normal)out<<a.sequence;else out<<"null";out<<",\"min_attempt\":";if(a.normal)out<<a.attempt;else out<<"null";out<<"}\n";++rows;}out.close();need(bool(out),"output close");std::cout<<rows<<" "<<count<<"\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
