// Independent whole-record reader, phase/NET/node counter transpose.
#include <array>
#include <fstream>
#include <iostream>
#include <map>
#include <tuple>
#include <vector>
#include <cstdint>
#include <stdexcept>
using U=uint64_t;using Row=std::array<U,18>;
int main(int argc,char** argv){try{if(argc!=3)throw std::runtime_error("file and ready required");U ready=std::stoull(argv[2]);std::ifstream f(argv[1],std::ios::binary);char h[8];f.read(h,8);if(std::string(h,8)!="RCFRNT01")throw std::runtime_error("magic");std::map<std::tuple<U,U,U>,std::array<U,2>> counts;std::vector<Row> block(16384);
while(f){f.read((char*)block.data(),block.size()*sizeof(Row));auto bytes=f.gcount();if(bytes%sizeof(Row))throw std::runtime_error("tail");for(U j=0;j<U(bytes/sizeof(Row));++j){auto& r=block[j];if((r[1]==ready||r[1]+1==ready)&&(r[0]==1||r[0]==3))++counts[{r[1],r[2],r[7]}][r[0]==1?0:1];}}
if(!f.eof())throw std::runtime_error("read error");for(auto& kv:counts){auto [i,net,node]=kv.first;std::cout<<i<<'\t'<<net<<'\t'<<node<<'\t'<<kv.second[0]<<'\t'<<kv.second[1]<<'\n';}return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
