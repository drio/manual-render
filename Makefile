CC = clang
CFLAGS = -Wall -std=c99 -I$(HOME)/dev/github.com/raysan5/raylib-5.5/src
LIBS = -L$(HOME)/dev/github.com/raysan5/raylib-5.5/src -lraylib -lm -lpthread -ldl -lrt -lX11
TOOL = manual-render

manual-render: main.c
	$(CC) $(CFLAGS) main.c -o $@ $(LIBS)

clean:
	rm -f $(TOOL)

lsp:
	rm -f compile_commands.json
	bear -- make clean
	bear -- make

float:
	make clean $(TOOL); float-launch ./$(TOOL)

.PHONY: clean lsp float
