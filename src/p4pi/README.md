This folder contains P4 code to run in a Raspberry Pi.

# Execution

- Follow [P4PI](https://github.com/p4lang/p4pi) to deploy and run [basic.p4](./basic.p4) inside a Raspberry Pi
- On another machine run the controller: `./controller.py --thrift-address 10.0.0.3:9090 --p4-runtime-address 10.0.0.3:50051  --block-class=1` to block traffic that is classifed as `1` on the Raspberry Pi which has IP `10.0.0.3`

* Note *
   By default, P4 runtime exposes only to local IP, thus you might need to 
   - either use SSH port forwarding to forward port 50051 from the controller machine to the Raspberry PI
   - or changing `--grpc-server-addr` value to `0.0.0.0:50051` in `/usr/bin/bmv2-start` file in the Raspberry PI, then restart the `bmv2` service.


- 