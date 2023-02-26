#include <iostream>
#include <iomanip>
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
        packet+=IP_HL(ip_hdr)<<2;

        string src(inet_ntoa(ip_hdr->ip_src));
        string dst(inet_ntoa(ip_hdr->ip_dst));
        uint16_t pkt_len(ntohs(ip_hdr->ip_len));
        pkt_len-=IP_HL(ip_hdr)<<2;

        switch(ip_hdr->ip_p){
        case 0x01:{
            sniff_icmp*icmp_hdr=(sniff_icmp*)packet;
            packet+=sizeof(icmp_hdr);

            cout<<"Transport type: ICMP"<<endl;
            cout<<"Source IP: "<<src<<endl;
            cout<<"Destination IP: "<<dst<<endl;
            cout<<"ICMP type value: "<<dec<<icmp_hdr->icmp_type<<endl;
            break;
        }case 0x06:{
            sniff_tcp*tcp_hdr=(sniff_tcp*)packet;
            packet+=TH_OFF(tcp_hdr)<<2;
            pkt_len-=TH_OFF(tcp_hdr)<<2;
            uint16_t sport=ntohs(tcp_hdr->th_sport);
            uint16_t dport=ntohs(tcp_hdr->th_dport);

            uint8_t*payload=(uint8_t*)packet;
            cout<<"Transport type: TCP"<<endl;
            cout<<"Source IP: "<<src<<endl;
            cout<<"Destination IP: "<<dst<<endl;
            cout<<"Source Port: "<<sport<<endl;
            cout<<"Destination Port: "<<dport<<endl;
            cout<<"Payload: ";
            for(int i=0;i<min((uint16_t)16,pkt_len);++i)
                cout<<hex<<(int)payload[i]<<' ';
            cout<<endl;
            break;
        }case 0x11:{
            sniff_udp*udp_hdr=(sniff_udp*)packet;
            packet+=sizeof(udp_hdr);
            pkt_len-=sizeof(udp_hdr);
            uint16_t sport=ntohs(udp_hdr->uh_sport);
            uint16_t dport=ntohs(udp_hdr->uh_dport);

            uint8_t*payload=(uint8_t*)packet;
            cout<<"Transport type: UDP"<<endl;
            cout<<"Source IP: "<<src<<endl;
            cout<<"Destination IP: "<<dst<<endl;
            cout<<"Source Port: "<<sport<<endl;
            cout<<"Destination Port: "<<dport<<endl;
            cout<<"Payload: ";
            for(int i=0;i<min((uint16_t)16,pkt_len);++i)
                cout<<hex<<setfill('0')<<setw(2)<<(int)payload[i]<<' ';
            cout<<endl;
            break;
        }default:{
            cout<<"Not implemented protocol"<<endl;
        }
        }
        cout<<endl;
    }
    pcap_close(handle);
    return 0;
}
