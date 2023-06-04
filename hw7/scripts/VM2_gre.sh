#!/bin/sh
sudo ovs-vsctl add-port s2 s2-gre1 -- set interface s2-gre1 type=gre options:remote_ip=10.8.0.6
