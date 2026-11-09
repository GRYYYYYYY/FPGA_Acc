#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
using U=uint64_t;
U read(std::ifstream& f){U x=0;for(int i=0;i<8;++i){int b=f.get();if(b==EOF)throw std::runtime_error("truncated u64");x|=U(b)<<(8*i);}return x;}
std::vector<U> vec(std::ifstream& f,U n){std::vector<U>a(n);for(auto&x:a)x=read(f);return a;}
void end(std::ifstream& f){if(f.peek()!=EOF)throw std::runtime_error("trailing data");}
int main(int argc,char**argv){try{
 if(argc<4)throw std::runtime_error("graph, sink:path arguments required");std::ifstream f(argv[1],std::ios::binary);if(read(f)!=2026100706)throw std::runtime_error("magic");U n=read(f),m=read(f);if(!n||n>100000000||m>1000000000)throw std::runtime_error("dimensions");auto off=vec(f,n+1),dst=vec(f,m),cap=vec(f,n),w=vec(f,m);end(f);if(off[0]||off[n]!=m)throw std::runtime_error("offset coverage");for(U u=0;u<n;++u)if(off[u]>off[u+1])throw std::runtime_error("offset order");for(U v:dst)if(v>=n)throw std::runtime_error("destination");U checked=0;const U inf=std::numeric_limits<U>::max();
 for(int k=2;k<argc;++k){std::string arg(argv[k]);auto pos=arg.find(':');if(pos==std::string::npos)throw std::runtime_error("sink:path");std::string s=arg.substr(0,pos);size_t used=0;U sink=std::stoull(s,&used);if(used!=s.size()||sink>=n||!cap[sink])throw std::runtime_error("sink");std::ifstream b(arg.substr(pos+1),std::ios::binary);auto d=vec(b,n);end(b);if(d[sink])throw std::runtime_error("target nonzero");for(U u=0;u<n;++u)for(U e=off[u];e<off[u+1];++e){U v=dst[e];if(cap[u]&&d[v]!=inf){if(d[u]==inf||w[e]>inf-d[v]||d[u]>w[e]+d[v])throw std::runtime_error("domain/inequality");++checked;}}}
 std::cout<<"{\"certificates\":"<<argc-2<<",\"inequality_arcs\":"<<checked<<"}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
