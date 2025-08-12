CC = clang
CFLAGS = -Wall -std=c99 -I$(HOME)/dev/github.com/raysan5/raylib-5.5/src
LIBS = -L$(HOME)/dev/github.com/raysan5/raylib-5.5/src -lraylib -lm -lpthread -ldl -lrt -lX11
TOOL = manual-render

# WebAssembly build settings
WEB_OUTPUT = web/index.html
RAYLIB_WEB_LIB = $(HOME)/dev/github.com/raysan5/raylib-5.5/build_web/raylib/libraylib.a

.PHONY: clean lsp float notebook watch lint format typecheck check fix web web-serve

manual-render: main.c
	$(CC) $(CFLAGS) main.c -o $@ $(LIBS)

# Build WebAssembly version
# https://github.com/raysan5/raylib/wiki/Working-for-Web-(HTML5)
web: main.c
	mkdir -p web
	emcc main.c $(RAYLIB_WEB_LIB) -o $(WEB_OUTPUT) \
		-Os -Wall \
		-s USE_GLFW=3 \
		-s ASYNCIFY \
		-s TOTAL_MEMORY=67108864 \
		-s FORCE_FILESYSTEM=1 \
		-DPLATFORM_WEB \
	    -g4 -s MINIFY_HTML=0  \
		-I $(HOME)/dev/github.com/raysan5/raylib-5.5/src
	cp html/index.html web/


# Serve the web version locally (requires Python)
web-serve: web
	@echo "Starting local server at http://localhost:8777"
	@cd web && python3 -m http.server 8787

.PHONY: raylib-web
raylib-web:
	cd ~/dev/github.com/raysan5/raylib-5.5/src;\
		mkdir build_web && cd build_web; \
		emcmake cmake .. -DPLATFORM=Web -DBUILD_EXAMPLES=OFF;\
		emmake make

clean:
	rm -f $(TOOL)
	rm -rf web/

lsp:
	rm -f compile_commands.json
	bear -- make clean
	bear -- make

float:
	make clean $(TOOL); sleep 1; float-launch ./$(TOOL)

run: 
	uv run python ./main.py

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
