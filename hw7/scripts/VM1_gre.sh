#!/bin/sh
sudo ovs-vsctl add-port s1 s1-gre1 -- set interface s1-gre1 type=gre options:remote_ip=10.8.0.7
