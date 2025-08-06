CC = clang
CFLAGS = -Wall -std=c99 -I$(HOME)/dev/github.com/raysan5/raylib-5.5/src
LIBS = -L$(HOME)/dev/github.com/raysan5/raylib-5.5/src -lraylib -lm -lpthread -ldl -lrt -lX11
TOOL = manual-render

.PHONY: clean lsp float notebook watch lint format typecheck check fix

manual-render: main.c
	$(CC) $(CFLAGS) main.c -o $@ $(LIBS)

clean:
	rm -f $(TOOL)

lsp:
	rm -f compile_commands.json
	bear -- make clean
	bear -- make

float:
	make clean $(TOOL); sleep 1; float-launch ./$(TOOL)

watch:
	uv run watchfiles ./main.py

notebook:
	uv run jupyter notebook

# Python code quality targets
lint:
	uv run ruff check .

format:
	uv run black .

typecheck:
	uv run mypy .

check: lint
	uv run black --check .

fix:
	uv run ruff check . --fix
	uv run black .
