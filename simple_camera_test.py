#!/usr/bin/env python3
"""
Simple Camera Test - Start from working triangle and add camera movement
"""

import ctypes
import math
import time

import glcontext
import moderngl
import numpy as np
import sdl2

# Simple vertex shader - just MVP transformation
VERTEX_SHADER = """
#version 330 core

in vec3 in_position;
in vec3 in_color;

uniform mat4 mvp_matrix;

out vec3 frag_color;

void main() {
    gl_Position = mvp_matrix * vec4(in_position, 1.0);
    frag_color = in_color;
}
"""

# Simple fragment shader
FRAGMENT_SHADER = """
#version 330 core

in vec3 frag_color;
out vec4 out_color;

void main() {
    out_color = vec4(frag_color, 1.0);
}
"""


def create_triangle():
    """Simple triangle - same as working shader_test.py"""
    vertices = np.array(
        [
            [-0.5, -0.5, 0.0, 1.0, 0.0, 0.0],  # Red
            [0.5, -0.5, 0.0, 1.0, 0.0, 0.0],
            [0.0, 0.5, 0.0, 1.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    return vertices


def setup_window_and_context():
    """
    GPU STEP 1: Create window and OpenGL context
    This establishes the connection to the graphics card
    """
    print("=== GPU STEP 1: Setting up window and OpenGL context ===")

    # Initialize SDL2 video subsystem
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        raise RuntimeError(f"SDL2 init failed: {sdl2.SDL_GetError()}")

    # Request OpenGL 3.3 Core Profile
    sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
    sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 3)
    sdl2.SDL_GL_SetAttribute(
        sdl2.SDL_GL_CONTEXT_PROFILE_MASK, sdl2.SDL_GL_CONTEXT_PROFILE_CORE
    )
    sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)

    # Create window
    width, height = 800, 600
    window = sdl2.SDL_CreateWindow(
        b"Simple Camera Test - GPU Pipeline Demo",
        sdl2.SDL_WINDOWPOS_CENTERED,
        sdl2.SDL_WINDOWPOS_CENTERED,
        width,
        height,
        sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_SHOWN,
    )

    if not window:
        raise RuntimeError(f"Window creation failed: {sdl2.SDL_GetError()}")

    # Create OpenGL context and make it current
    gl_context = sdl2.SDL_GL_CreateContext(window)
    if not gl_context:
        raise RuntimeError(f"OpenGL context creation failed: {sdl2.SDL_GetError()}")

    if sdl2.SDL_GL_MakeCurrent(window, gl_context) != 0:
        raise RuntimeError(
            f"Failed to make OpenGL context current: {sdl2.SDL_GetError()}"
        )

    # Create ModernGL context (high-level OpenGL wrapper)
    backend = glcontext.default_backend()
    gl_ctx = backend(mode="detect")
    ctx = moderngl.create_context(context=gl_ctx)

    print(f"✓ OpenGL Version: {ctx.version_code}")
    print(f"✓ Window created: {width}x{height}")

    return window, gl_context, ctx


def create_shader_program(ctx):
    """
    GPU STEP 2: Compile and link shaders into a program
    Shaders are small programs that run on the GPU
    """
    print("=== GPU STEP 2: Creating shader program ===")

    try:
        program = ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )
        print("✓ Vertex shader compiled successfully")
        print("✓ Fragment shader compiled successfully")
        print("✓ Shader program linked successfully")
        return program
    except Exception as e:
        print(f"✗ Shader compilation/linking failed: {e}")
        raise


def setup_vertex_data(ctx, program):
    """
    GPU STEP 3: Upload vertex data to GPU memory
    This creates buffers and describes the data layout
    """
    print("=== GPU STEP 3: Setting up vertex data on GPU ===")

    # Create triangle geometry
    vertices = create_triangle()
    print(f"✓ Created triangle with {len(vertices)} vertices")

    # Create Vertex Buffer Object (VBO) - uploads data to GPU memory
    vbo = ctx.buffer(vertices.tobytes())
    print("✓ Vertex Buffer Object (VBO) created - data uploaded to GPU")

    # Create Vertex Array Object (VAO) - describes how to interpret the data
    vao = ctx.vertex_array(
        program,
        [
            (vbo, "3f 3f", "in_position", "in_color")
            # '3f 3f' means: 3 floats for position, 3 floats for color
        ],
    )
    print("✓ Vertex Array Object (VAO) created - data layout defined")

    return vao


def run_render_loop(window, ctx, program, vao):
    """
    GPU STEP 4: Main render loop
    This runs every frame to draw the triangle
    """
    print("=== GPU STEP 4: Starting render loop ===")
    print("Controls: SPACE = change test phase, ESC = exit")

    # Test matrices for learning
    identity_matrix = np.eye(4, dtype=np.float32)
    running = True
    event = sdl2.SDL_Event()
    test_phase = 0
    start_time = time.time()

    while running:
        # Handle input events
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False
                elif event.key.keysym.sym == sdl2.SDLK_SPACE:
                    test_phase = (test_phase + 1) % 3
                    phases = ["Identity Matrix", "Translation", "Rotation"]
                    print(f"Switched to: {phases[test_phase]}")

        current_time = time.time() - start_time

        # Create different transformation matrices for learning
        if test_phase == 0:
            # Test 1: Identity matrix - no transformation
            mvp_matrix = identity_matrix

        elif test_phase == 1:
            # Test 2: Translation matrix - move triangle left/right
            translation = math.sin(current_time) * 0.5
            mvp_matrix = np.array(
                [
                    [1, 0, 0, translation],  # X translation in last column
                    [0, 1, 0, 0],  # Y unchanged
                    [0, 0, 1, 0],  # Z unchanged
                    [0, 0, 0, 1],  # Homogeneous coordinate
                ],
                dtype=np.float32,
            )

        else:
            # Test 3: Rotation matrix - rotate triangle around Z axis
            angle = current_time * 2.0
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            mvp_matrix = np.array(
                [
                    [cos_a, -sin_a, 0, 0],  # 2D rotation matrix
                    [sin_a, cos_a, 0, 0],  # in 4x4 homogeneous form
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ],
                dtype=np.float32,
            )

        # RENDER FRAME:
        # 1. Send transformation matrix to GPU shader
        program["mvp_matrix"].write(mvp_matrix.tobytes())

        # 2. Clear the screen (background color)
        ctx.clear(0.2, 0.3, 0.3, 1.0)  # Dark teal background

        # 3. Draw the triangle (GPU runs shaders for each vertex/pixel)
        vao.render()

        # 4. Present the frame (swap front/back buffers)
        sdl2.SDL_GL_SwapWindow(window)

        # Control frame rate (~60 FPS)
        sdl2.SDL_Delay(16)

    print("✓ Render loop finished")


def cleanup(window, gl_context):
    """Clean up SDL2 and OpenGL resources"""
    print("=== Cleaning up GPU resources ===")
    sdl2.SDL_GL_DeleteContext(gl_context)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    print("✓ All resources cleaned up")


def main():
    """
    Main function demonstrating the 4-step GPU shader pipeline:
    1. Setup window and OpenGL context
    2. Create and compile shader program
    3. Upload vertex data to GPU
    4. Run render loop
    """
    print("=== SIMPLE CAMERA TEST - GPU SHADER PIPELINE DEMO ===")
    print("This demonstrates the 4 essential steps to use GPU shaders\n")

    try:
        # Step 1: Connect to GPU and create rendering context
        window, gl_context, ctx = setup_window_and_context()

        # Step 2: Create shader program (vertex + fragment shaders)
        program = create_shader_program(ctx)

        # Step 3: Upload triangle data to GPU memory
        vao = setup_vertex_data(ctx, program)

        # Step 4: Run the main rendering loop
        run_render_loop(window, ctx, program, vao)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always clean up resources
        cleanup(window, gl_context)


if __name__ == "__main__":
    main()

