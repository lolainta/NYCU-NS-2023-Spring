#include <iostream>
#include <stdlib.h>
#include <pcap/pcap.h> 
#include <string.h>
#include <vector>
using namespace std;

int main(int argc, const char * argv[]) 
{
    pcap_if_t *devices = NULL; 
    char errbuf[PCAP_ERRBUF_SIZE];
    char ntop_buf[256];
    struct ether_header *eptr;
    vector<pcap_if_t*> vec; // vec is a vector of pointers pointing to pcap_if_t 
    
    //get all devices 
    if(-1 == pcap_findalldevs(&devices, errbuf)) {
        fprintf(stderr, "pcap_findalldevs: %s\n", errbuf); // if error, fprint error message --> errbuf
        exit(1);
    }

    //list all device
    int cnt = 0;
    for(pcap_if_t *d = devices; d ; d = d->next, cnt++)
    {
        vec.push_back(d);
        cout<<"Name: "<<d->name<<endl;
    }

    struct bpf_program fp; // for filter, compiled in "pcap_compile"
    pcap_t *handle;
    handle = pcap_open_live({your_interface}, 65535, 1, 1, errbuf);  
    //pcap_open_live(device, snaplen, promise, to_ms, errbuf), interface is your interface, type is "char *"   
    

    if(!handle|| handle == NULL)
    {
        fprintf(stderr, "pcap_open_live(): %s\n", errbuf);
        exit(1);
    }
 
    if(-1 == pcap_compile(handle, &fp, {your_filter}, 1, PCAP_NETMASK_UNKNOWN) ) // compile "your filter" into a filter program, type of {your_filter} is "char *"
    {
        pcap_perror(handle, "pkg_compile compile error\n");
        exit(1);
    }
    if(-1 == pcap_setfilter(handle, &fp)) { // make it work
        pcap_perror(handle, "set filter error\n");
        exit(1);
    }

    while(1) 
    {   
        const unsigned char* packet = pcap_next(handle, &header);
    }

    pcap_freealldevs(devices);

    return 0;
    
}