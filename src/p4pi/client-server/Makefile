CC = gcc
ARGS = -Wall -O0 -g -I .

all: server client

server: server.c
	$(CC) $(ARGS) -o server server.c

client: client.c
	$(CC) $(ARGS) -o client client.c

clean:
	rm -f *.o server client *~
