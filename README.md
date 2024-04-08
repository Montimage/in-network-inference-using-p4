# inline-traffic-classification-using-p4
A ML-based inline traffic classification using P4

This repository implements a machine-learning-based approach to classify encrypted network traffic using P4. The testbed is evaluated on a P4 virtual device, [BMv2 Simple Switch](https://github.com/p4lang/behavioral-model/blob/main/docs/simple_switch.md). The model is [Decision Tree Classifier](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html) using 2 features which are independent of packets' payload (that is encrypted) :

- `iat` (Inter-Arrival Time): different arrival time of the current packet and the one of the previous packet
- `len`: total length of the current IP packet

The source code consists mainly 2 parts:

- [offline](./src/offline) contains tools to extract features from pcap files, train model, evaluate model and generate P4 match-action tables' entries
- [bmv2](./src/bmv2) contains P4 code to run BMv2 switch which performs the infererence of the DT model against network traffic



# Execution

The execution can be performed basically in 2 steps as below.

## Model preparation

```bash
cd ./bmv2/offline
# extract iat and len features from pcap files in ./pcaps folder
././process_pcaps.py

# train a DT model using the features above
 ./train_model.py

# generate match-action table's entries to configure P4 switch
./generate_table_entries.py 
```

## Inference

See prerequisites [here](./src/bmv2#prerequisite)

```bash
cd ./src/bmv2
# start P4 switch
make run

# open a new terminal, start the controller which will:
# - configure the switch within the table's entries generated above
# - receive inference output from the switch
./controller.py

# back to the first terminal of P4 switch, use tcpreplay to generate some traffic
mininet> sh tcpreplay -i s1-eth1  --preload-pcap --timer=gtod ../offline/pcaps/skype.v2.pcap
```

An output of the `controller.py` is as the following:

```bash
src/bmv2$ ./controller.py 
Configuring switch with file ../offline/pcaps/s1-commands.txt
E0408 17:48:33.927385753   58549 fork_posix.cc:63]           Fork support is only compatible with the epoll1 and poll polling strategies
192.168.1.34 157.55.130.153 50057 443 6 => 0 64 => unknown
157.55.130.153 192.168.1.34 443 50057 6 => 65531 60 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65527 52 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65607 124 => skype
157.55.130.153 192.168.1.34 443 50057 6 => 65463 52 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65569 86 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65535 86 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65535 86 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65535 86 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65535 86 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65535 86 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65501 52 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65569 86 => skype
157.55.130.153 192.168.1.34 443 50057 6 => 65542 93 => skype
192.168.1.34 157.55.130.153 50057 443 6 => 65482 40 => skype
^CBye.
```
