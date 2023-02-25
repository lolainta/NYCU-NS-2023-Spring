#include <iostream>
#include <cassert>
#include <getopt.h>
#include <pcap/pcap.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>

#include "headers.h"

using namespace std;
using str=string;

char errbuf[PCAP_ERRBUF_SIZE];

void usage(char*p){
    cout<<"Usage:\n\t";
    cout<<p<<" [-i|--interface <interface name>] [-c|--count <number of packets>] [-f|--filter <filters>]"<<endl;
}

void process_arguments(int argc,char*argv[],string&iface,int&count,string&filter){
    const char*sopts="i:c:f:";
    const option lopts[]={
        {"interface",required_argument,nullptr,'i'},
        {"count",required_argument,nullptr,'c'},
        {"filter",required_argument,nullptr,'f'}
    };
    count=-1;
    iface="any";
    filter="all";
    for(;;){
        const auto opt=getopt_long(argc,argv,sopts,lopts,nullptr);
        if(opt==-1)
            break;
        switch(opt){
        case 'i':
            iface=optarg;
            break;
        case 'c':
            count=stoi(optarg);
            break;
        case 'f':
            filter=optarg;
            break;
        default:
            usage(argv[0]);
            exit(1);
        }
    }
    if(iface=="any"){
        usage(argv[0]);
        cerr<<"You need to specify an interface!"<<endl;
        exit(1);
    }
    if(filter=="all")
        filter.clear();
    return;
    bool check=false;
    pcap_if_t*devs=nullptr;
    if(pcap_findalldevs(&devs,errbuf)==-1){
        perror("pcap_findalldevs");
        cerr<<errbuf<<endl;
        exit(1);
    }
    for(pcap_if_t*dev=devs;dev;dev=dev->next){
        if(str(dev->name)==iface.c_str())
            check=true;
    }
    if(!check){
        cerr<<"Unknown interface!"<<endl;
        exit(1);
    }
}

void hexdump(uint8_t*msg,int sz){
    int cnt=0;
    for(int i=0;i<sz;++i,++cnt){
        if(cnt%8==0 and i)
            cout<<endl;
        cout<<hex<<(int)msg[i]<<' ';
    }
    cout<<endl;
}

int main(int argc,char*argv[]){
    int count;
    string iface,filter;
    process_arguments(argc,argv,iface,count,filter);

    pcap_t*handle;
    if((handle=pcap_open_live(iface.c_str(),65535,1,1,errbuf))==nullptr){
        perror("pcap_open_live");
        cerr<<errbuf<<endl;
        exit(1);
    }

    cout<<filter<<endl;
    bpf_program fp;
    if(pcap_compile(handle,&fp,filter.c_str(),1,PCAP_NETMASK_UNKNOWN)==-1){
        pcap_perror(handle,"pcap_compile");
        exit(1);
    }
    if(pcap_setfilter(handle,&fp)==-1){
        pcap_perror(handle,"pcap_setfilter");
        exit(1);
    }

    for(int i=0;i<count || count==-1;++i){
        pcap_pkthdr hdr;
        const u_char*packet=pcap_next(handle,&hdr);
        if(packet==nullptr){
            perror("pcap_next");
            exit(1);
        }
        assert(hdr.caplen==hdr.len);

        // sniff_ethernet*eth_hdr=(sniff_ethernet*)packet;
        packet+=SIZE_ETHERNET;

        sniff_ip*ip_hdr=(sniff_ip*)packet;
        packet+=20;
        switch(ip_hdr->ip_p){
        case 0x01:
            cout<<"ICMP"<<endl;
            break;
        case 0x06:
            cout<<"TCP"<<endl;
            break;
        case 0x11:
            cout<<"UDP"<<endl;
            break;
        default:
            cout<<"Not implemented protocol"<<endl;
        }
        cout<<"==================="<<endl;
    }

    pcap_close(handle);

    return 0;
}
