CC = clang
CFLAGS = -Wall -std=c99
LIBS = -lX11
TOOL = toyx11

toyx11: main.c
	$(CC) $(CFLAGS) main.c -o $@ $(LIBS)

clean:
	rm -f $(TOOL) compile_commands.json

lsp:
	bear -- make clean
	bear -- make

.PHONY: clean lsp
