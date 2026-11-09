// Independent byte-stream FNV1a64 over captured payload after its 24-byte header.
#include <fstream>
#include <iostream>
#include <cstdint>
int main(int argc,char** argv){for(int i=1;i<argc;++i){std::ifstream f(argv[i],std::ios::binary);if(!f)return 2;f.seekg(24);std::uint64_t h=14695981039346656037ULL;char buffer[65536];while(f){f.read(buffer,sizeof(buffer));for(std::streamsize j=0;j<f.gcount();++j){h^=static_cast<unsigned char>(buffer[j]);h*=1099511628211ULL;}}if(!f.eof())return 3;std::cout<<h<<'\n';}return 0;}
