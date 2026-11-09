// Pinned native scalar present-cost expression, after explicit one-owner release.
#include <iostream>
#include <cstdint>
#include <cstring>
int main(){unsigned long long id;int occupancy,capacity,owned;uint32_t bits;while(std::cin>>id>>occupancy>>capacity>>owned>>bits){if(capacity<=0||(owned!=0&&owned!=1)||occupancy<owned)return 2;float pres;std::memcpy(&pres,&bits,4);int occ=occupancy-owned;float price;if(occ>=capacity)price=(1.+pres*(occ+1-capacity));else price=1.;uint32_t result;std::memcpy(&result,&price,4);std::cout<<id<<' '<<result<<'\n';}return std::cin.eof()?0:3;}
