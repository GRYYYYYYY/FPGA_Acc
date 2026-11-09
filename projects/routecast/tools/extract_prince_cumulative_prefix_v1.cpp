// Independent full-record counter and explicit first/last minima/maxima.
#include <array>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#include <cstdint>
#include <stdexcept>
using U=uint64_t;using Row=std::array<U,18>;
int main(int argc,char**argv){try{if(argc!=3)throw std::runtime_error("file cutoff");U cut=std::stoull(argv[2]);std::ifstream f(argv[1],std::ios::binary);char h[8];f.read(h,8);if(std::string(h,8)!="RCFRNT01")throw std::runtime_error("header");std::map<std::pair<U,U>,std::array<U,8>> history;std::vector<Row> block(16384);
while(f){f.read((char*)block.data(),block.size()*sizeof(Row));auto bytes=f.gcount();if(bytes%sizeof(Row))throw std::runtime_error("tail");for(U j=0;j<U(bytes/sizeof(Row));++j){auto&r=block[j];if(r[1]<1||r[1]>cut||cut>=64)throw std::runtime_error("cutoff");if(r[0]!=1&&r[0]!=3)continue;auto&a=history[{r[2],r[7]}];int k=r[0]==1?0:4;++a[k];a[k+1]|=U(1)<<(r[1]-1);if(!a[k+2]||r[1]<a[k+2])a[k+2]=r[1];if(r[1]>a[k+3])a[k+3]=r[1];}}
if(!f.eof())throw std::runtime_error("read error");for(auto&kv:history){std::cout<<kv.first.first<<'\t'<<kv.first.second;for(U x:kv.second)std::cout<<'\t'<<x;std::cout<<'\n';}return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
