This folder contains P4 code to run in a Raspberry Pi.

# Execution

- Follow [P4PI](https://github.com/p4lang/p4pi) to deploy and run [basic.p4)(./basic.p4) inside a Raspberry Pi
- On another machine run the controller: `./controller.py --thrift-address 10.0.0.3:9090 --p4-runtime-address 10.0.0.3:50051  --block-class=1` to block traffic that is classifed as `1` on the Raspberry Pi which has IP `10.0.0.3`
