#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
using U=std::uint64_t;
U read64(std::istream& s){unsigned char b[8];if(!s.read(reinterpret_cast<char*>(b),8))throw std::runtime_error("truncated graph");U v=0;for(int i=7;i>=0;--i)v=(v<<8)|b[i];return v;}
U number(const char* p){std::string s(p);if(s.empty()||s.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("invalid integer");size_t used=0;U v=std::stoull(s,&used);if(used!=s.size())throw std::runtime_error("invalid integer");return v;}
int main(int argc,char** argv){try{
 if(argc<5)throw std::runtime_error("graph cutoff output-directory sinks...");
 std::ifstream graph(argv[1],std::ios::binary);if(!graph)throw std::runtime_error("cannot open graph");
 if(read64(graph)!=2026100706ULL)throw std::runtime_error("wrong graph magic");
 U n=read64(graph),m=read64(graph),cap=number(argv[2]);
 if(!n||!cap||n>std::numeric_limits<size_t>::max()/8||m>std::numeric_limits<size_t>::max()/16)throw std::runtime_error("invalid dimensions or cutoff");
 auto read=[&](U count){std::vector<U> a(count);for(auto& v:a)v=read64(graph);return a;};auto offsets=read(n+1),dest=read(m),capacities=read(n),weights=read(m);
 if(offsets[0]||offsets.back()!=m||!std::is_sorted(offsets.begin(),offsets.end())||std::any_of(dest.begin(),dest.end(),[&](U d){return d>=n;})||graph.peek()!=std::char_traits<char>::eof())throw std::runtime_error("invalid graph arrays");
 std::vector<std::vector<std::pair<U,U>>> reverse(n);for(U u=0;u<n;++u)for(U e=offsets[u];e<offsets[u+1];++e)reverse[dest[e]].emplace_back(u,weights[e]);
 const std::filesystem::path output(argv[3]);if(!std::filesystem::is_directory(output))throw std::runtime_error("output directory missing");U certificates=0;
 for(int argument=4;argument<argc;++argument){U sink=number(argv[argument]);if(sink>=n||!capacities[sink])throw std::runtime_error("invalid sink");auto file=output/("sink"+std::to_string(sink)+".bin");if(std::filesystem::exists(file))throw std::runtime_error("existing output");
  std::vector<U> distances(n,cap);distances[sink]=0;using Item=std::pair<U,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;queue.emplace(0,sink);
  while(!queue.empty()){auto [distance,v]=queue.top();queue.pop();if(distance!=distances[v])continue;for(auto [u,w]:reverse[v]){if(!capacities[u])continue;U next=w>cap-distance?cap:distance+w;if(next<distances[u]){distances[u]=next;queue.emplace(next,u);}}}
  std::vector<char> bytes(n*8);for(U u=0;u<n;++u){U v=distances[u];for(int b=0;b<8;++b){bytes[u*8+b]=char(v&255);v>>=8;}}
  std::ofstream stream(file,std::ios::binary);if(!stream.write(bytes.data(),bytes.size()))throw std::runtime_error("write failure");stream.close();if(!stream)throw std::runtime_error("close failure");++certificates;
 }
 std::cout<<"{\"publications\":"<<certificates<<"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}}
