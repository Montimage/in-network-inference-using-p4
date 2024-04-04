This folder contains a simpified version of [Basic Forwarding](https://github.com/p4lang/tutorials/blob/d007dc4b95200afd6f9b7055fbc9cc7ff927ef35/exercises/basic/README.md).

It is to create a simple network using Mininet. The network consists of 2 hosts, 
`h1`, `h2`, and a switch `s1` between these hosts. The switch runs [basic.p4](./basic.p4) program.


```
   (h1) ======= (  s1  ) ======= (h2)
10.0.1.1      port1  port2     10.0.2.2
```

# Prerequisite
   The following requirements are for Ubuntu 20.04 server. Otherwise, please see details [here](https://github.com/p4lang/tutorials#obtaining-required-software)

1. BMv2 + P4c
   ```bash
   . /etc/os-release
   echo "deb http://download.opensuse.org/repositories/home:/p4lang/xUbuntu_${VERSION_ID}/ /" | sudo tee /etc/apt/sources.list.d/home:p4lang.list
   curl -fsSL "https://download.opensuse.org/repositories/home:p4lang/xUbuntu_${VERSION_ID}/Release.key" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/home_p4lang.gpg > /dev/null
   sudo apt update
   sudo apt install -y p4lang-bmv2 p4lang-p4c
   ```

   Further details [here](https://github.com/p4lang/behavioral-model?tab=readme-ov-file#installing-bmv2)
   and [here](https://github.com/p4lang/p4c?tab=readme-ov-file#ubuntu)

2. Mininet
   ```bash
   sudo apt install -y mininet
   ```

   Further details [here](https://mininet.org/download/#option-3-installation-from-packages)

3. Others
   ```bash
   sudo apt update && sudo apt install -y make python3-pip
   sudo pip3 install mininet psutil
   ```


# Basic Test
1. In your shell, run:
   ```bash
   make run
   ```
   This will:
   * compile `basic.p4`, and
   * start the pod-topo in Mininet and configure the switch with
   the appropriate P4 program + table entries, and
   * configure all hosts with the commands listed in
   [topology.json](./topology.json)

2. You should now see a Mininet command prompt. Try to ping between
   hosts in the topology:
   ```bash
   mininet> h1 ping h2
   mininet> pingall
   ```

   Example:
   ```
   mininet> h2 ping h1
   PING 10.0.1.1 (10.0.1.1) 56(84) bytes of data.
   64 bytes from 10.0.1.1: icmp_seq=1 ttl=63 time=13.5 ms
   64 bytes from 10.0.1.1: icmp_seq=2 ttl=63 time=13.1 ms
   64 bytes from 10.0.1.1: icmp_seq=3 ttl=63 time=14.9 ms
   64 bytes from 10.0.1.1: icmp_seq=4 ttl=63 time=12.0 ms
   64 bytes from 10.0.1.1: icmp_seq=5 ttl=63 time=13.4 ms
   64 bytes from 10.0.1.1: icmp_seq=6 ttl=63 time=12.7 ms
   64 bytes from 10.0.1.1: icmp_seq=7 ttl=63 time=12.6 ms
   ^C
   --- 10.0.1.1 ping statistics ---
   7 packets transmitted, 7 received, 0% packet loss, time 6019ms
   rtt min/avg/max/mdev = 11.988/13.167/14.910/0.852 ms
   mininet> pingall
   *** Ping: testing ping reachability
   h1 -> h2 
   h2 -> h1 
   *** Results: 0% dropped (2/2 received)
   ```

3. To exit, type `exit` to leave each xterm and the Mininet command line.
   Then, to stop mininet:
   ```bash
   make stop
   ```
   And to delete all pcaps, build files, and logs:
   ```bash
   make clean
   ```
