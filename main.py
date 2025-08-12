#!./.venv/bin/python
import ctypes
import logging
import math
import time

import numpy as np
import sdl2
import sdl2.ext

from fps import FPSCounter
from projection import project_3d_to_2d_direct, project_3d_to_2d_via_matrix
from rasterization import (
    clear_z_buffer,
    init_z_buffer,
    rasterize_triangle,
    rasterize_triangle_with_depth,
)

# Initialize SDL2
sdl2.ext.init()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Colors for cube triangles
RED_COLOR = (255, 100, 100)  # Red
BLUE_COLOR = (100, 100, 255)  # Blue
YELLOW_COLOR = (255, 255, 100)  # Yellow
GREEN_COLOR = (100, 255, 100)  # Green
MAGENTA_COLOR = (255, 100, 255)  # Magenta
CYAN_COLOR = (100, 255, 255)  # Cyan

# Other colors
DARK_GRAY_COLOR = (60, 60, 60)  # Ground plane
WHITE_COLOR = (255, 255, 255)  # White cube tint
LIGHT_RED_COLOR = (255, 200, 200)  # Large cube tint
LIGHT_GREEN_COLOR = (200, 255, 200)  # Small cube tint
PURE_RED_COLOR = (255, 0, 0)  # X axis
PURE_GREEN_COLOR = (0, 255, 0)  # Y axis
PURE_BLUE_COLOR = (0, 0, 255)  # Z axis


def setup_display_and_renderer():
    """
    RENDER STEP 1: Create display surface and rendering context
    This creates the output surface - will be replaced with OpenGL context later
    """
    print("=== RENDER STEP 1: Setting up display and rendering context ===")

    WIDTH, HEIGHT = 800, 600
    X, Y = 3025, 48  # Window position

    # Create window
    window = sdl2.ext.Window("3D Scene with Ground Plane - SDL2", size=(WIDTH, HEIGHT))
    sdl2.SDL_SetWindowPosition(window.window, X, Y)
    window.show()

    # Create renderer (will become OpenGL context later)
    renderer = sdl2.ext.Renderer(window)

    # Initialize z-buffer for depth testing
    init_z_buffer(WIDTH, HEIGHT)

    print(f"✓ Display created: {WIDTH}x{HEIGHT}")
    print("✓ Software renderer created (will become OpenGL context)")
    print("✓ Z-buffer initialized for depth testing")

    return window, renderer, WIDTH, HEIGHT


# Create window and renderer - will be moved to main() function
WIDTH, HEIGHT = 800, 600


class Camera:
    """Simple camera class to group camera-related variables"""

    def __init__(self, position=None, target=None, focal_length=500):
        self.position = position if position is not None else [-500, -300, 500]
        self.target = target if target is not None else [0, 50, 0]
        self.focal_length = focal_length

    def update_orbit(self, angle, radius=300, height=200):
        """Update camera position to orbit around the target"""
        # Calculate new position using circular motion
        self.position[0] = radius * math.cos(angle)  # X position
        self.position[1] = height  # Y position (constant)
        self.position[2] = radius * math.sin(angle)  # Z position


# Geometry definitions (shared by all instances of the same type)
# Provides a template to create cube instances
# values in tuples or lists reference the vertices
cube_geometry = {
    "vertices": [
        [-1, -1, -1],  # 0: back bottom left
        [1, -1, -1],  # 1: back bottom right
        [1, 1, -1],  # 2: back top right
        [-1, 1, -1],  # 3: back top left
        [-1, -1, 1],  # 4: front bottom left
        [1, -1, 1],  # 5: front bottom right
        [1, 1, 1],  # 6: front top right
        [-1, 1, 1],  # 7: front top left
    ],
    "edges": [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),  # back face
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),  # front face
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),  # connecting edges
    ],
    "triangles": [
        # Front face (z = 1): vertices [4, 5, 6, 7] - working triangle arrangement
        {"vertices": [4, 5, 7], "color": RED_COLOR, "name": "front_1"},
        {"vertices": [5, 6, 7], "color": RED_COLOR, "name": "front_2"},
        # Back face (z = -1): vertices [0, 1, 2, 3]
        {"vertices": [0, 2, 1], "color": BLUE_COLOR, "name": "back_1"},
        {"vertices": [0, 3, 2], "color": BLUE_COLOR, "name": "back_2"},
        # Top face (y = 1): vertices [2, 3, 7, 6]
        {"vertices": [2, 6, 7], "color": YELLOW_COLOR, "name": "top_1"},
        {"vertices": [2, 7, 3], "color": YELLOW_COLOR, "name": "top_2"},
        # Bottom face (y = -1): vertices [0, 1, 5, 4]
        {"vertices": [0, 4, 5], "color": GREEN_COLOR, "name": "bottom_1"},
        {"vertices": [0, 5, 1], "color": GREEN_COLOR, "name": "bottom_2"},
        # Left face (x = -1): vertices [0, 3, 7, 4]
        {"vertices": [0, 3, 7], "color": MAGENTA_COLOR, "name": "left_1"},
        {"vertices": [0, 7, 4], "color": MAGENTA_COLOR, "name": "left_2"},
        # Right face (x = 1): vertices [1, 2, 6, 5]
        {"vertices": [1, 5, 6], "color": CYAN_COLOR, "name": "right_1"},
        {"vertices": [1, 6, 2], "color": CYAN_COLOR, "name": "right_2"},
    ],
}

ground_plane_geometry = {
    # Base unit grid square from (-1,-1) to (1,1) on XZ plane
    "vertices": [
        [-1, 0, -1],  # 0: back left
        [1, 0, -1],  # 1: back right
        [1, 0, 1],  # 2: front right
        [-1, 0, 1],  # 3: front left
    ],
    "triangles": [
        {"vertices": [0, 1, 2], "color": DARK_GRAY_COLOR, "name": "grid_1"},
        {"vertices": [0, 2, 3], "color": DARK_GRAY_COLOR, "name": "grid_2"},
    ],
}

vertical_plane_geometry = {
    # Simple vertical plane facing positive Z direction (toward camera when camera is at negative Z)
    "vertices": [
        [-1, 0, 0],  # 0: bottom left
        [1, 0, 0],  # 1: bottom right
        [1, 1, 0],  # 2: top right
        [-1, 1, 0],  # 3: top left
    ],
    "triangles": [
        {"vertices": [0, 1, 2], "color": RED_COLOR, "name": "plane_1"},
        {"vertices": [0, 2, 3], "color": GREEN_COLOR, "name": "plane_2"},
    ],
}

axes_geometry = {
    "length": 200,
    "colors": {
        "x": PURE_RED_COLOR,  # Red (+x RIGHT)
        "y": PURE_GREEN_COLOR,  # Green (-y DOWN)
        "z": PURE_BLUE_COLOR,  # Blue (+z toward camera when facing origin)
    },
}


def create_cube_vertices(scale=50):
    """Create cube vertices with given scale"""
    return np.array(cube_geometry["vertices"]) * scale


def create_ground_plane_triangles(size=400, spacing=50):
    """Create triangles for a grid-based ground plane

    Args:
        size: Half-width of the plane (creates plane from -size to +size)
        spacing: Distance between grid lines

    Returns:
        List of triangle dictionaries with world-space vertices
    """
    triangles = []

    # Create a grid of squares, each split into 2 triangles
    for x in range(-size, size, spacing):
        for z in range(-size, size, spacing):
            # Define corners of current grid square
            p1 = [x, 0, z]  # bottom-left
            p2 = [x + spacing, 0, z]  # bottom-right
            p3 = [x + spacing, 0, z + spacing]  # top-right
            p4 = [x, 0, z + spacing]  # top-left

            # Alternate between the two triangle colors from geometry
            triangle1_color = ground_plane_geometry["triangles"][0][
                "color"
            ]  # BLUE_COLOR
            triangle2_color = ground_plane_geometry["triangles"][1][
                "color"
            ]  # YELLOW_COLOR

            # Split square into two triangles using geometry colors
            triangles.append({"vertices": [p1, p2, p3], "color": triangle1_color})
            triangles.append({"vertices": [p1, p3, p4], "color": triangle2_color})

    return triangles


def create_vertical_plane_triangles(size=100):
    """Create triangles for a vertical plane

    Args:
        size: Half-width/height of the plane

    Returns:
        List of triangle dictionaries with world-space vertices
    """
    # Scale the base geometry
    triangles = []
    for triangle in vertical_plane_geometry["triangles"]:
        # Scale vertices by size
        scaled_vertices = []
        for vertex_idx in triangle["vertices"]:
            vertex = vertical_plane_geometry["vertices"][vertex_idx]
            scaled_vertex = [vertex[0] * size, vertex[1] * size, vertex[2] * size]
            scaled_vertices.append(scaled_vertex)

        triangles.append({"vertices": scaled_vertices, "color": triangle["color"]})

    return triangles


def create_scene_objects():
    """
    RENDER STEP 2: Create 3D scene geometry and objects
    This defines all the objects that will be rendered - will work with both CPU and GPU rendering
    """
    print("=== RENDER STEP 2: Creating 3D scene objects ===")

    scene_objects = [
        {
            "type": "ground_plane",
            "pos": [0, 0, 0],
            "size": 400,
            "spacing": 50,
            "color": DARK_GRAY_COLOR,
            "name": "ground",
        },
        # {
        #     "type": "cube",
        #     "pos": [0, -50, 0],
        #     "scale": 50,
        #     "color": WHITE_COLOR,
        #     "name": "center_cube",
        # },
        {
            "type": "vertical_plane",
            "pos": [0, 0, 0],
            "size": 100,
            "color": RED_COLOR,
            "name": "front_plane",
        },
        {
            "type": "vertical_plane",
            "pos": [0, 0, -150],  # Behind the first plane
            "size": 80,
            "color": BLUE_COLOR,
            "name": "back_plane",
        },
        {
            "type": "axes",
            "pos": [0, 0, 0],
            "name": "coordinate_axes",
        },
    ]

    print(f"✓ Created {len(scene_objects)} scene objects")
    for obj in scene_objects:
        print(f"  - {obj['name']}: {obj['type']}")

    return scene_objects


def draw_circle_filled(renderer, x, y, radius):
    """Draw a filled circle using SDL2"""
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                renderer.draw_point((x + dx, y + dy))


def apply_color_tint(base_color, tint, intensity=0.3):
    """Apply a color tint to a base color"""
    r = int(base_color[0] * (1 - intensity) + tint[0] * intensity)
    g = int(base_color[1] * (1 - intensity) + tint[1] * intensity)
    b = int(base_color[2] * (1 - intensity) + tint[2] * intensity)
    return (min(255, r), min(255, g), min(255, b))


def draw_ground_plane(renderer, camera, size=400, spacing=50):
    """Draw ground plane with triangles and/or wireframe based on render flags"""

    # Draw filled triangles
    if RENDER_TRIANGLES:
        triangles = create_ground_plane_triangles(size, spacing)
        for triangle in triangles:
            # Project triangle vertices to 2D with depth
            p1_result = project_3d_to_2d(triangle["vertices"][0], camera)
            p2_result = project_3d_to_2d(triangle["vertices"][1], camera)
            p3_result = project_3d_to_2d(triangle["vertices"][2], camera)

            # Only render if all vertices are visible
            if p1_result and p2_result and p3_result:
                # Extract 2D positions and depths
                p1, z1 = (p1_result[0], p1_result[1]), p1_result[2]
                p2, z2 = (p2_result[0], p2_result[1]), p2_result[2]
                p3, z3 = (p3_result[0], p3_result[1]), p3_result[2]

                render_triangle(renderer, p1, p2, p3, triangle["color"], z1, z2, z3)

    # Draw wireframe grid
    if RENDER_WIREFRAME:
        renderer.color = sdl2.ext.Color(80, 80, 80, 255)  # Dark gray

        # Create grid lines parallel to X axis
        for z in range(-size, size + spacing, spacing):
            start_point = np.array([-size, 0, z])
            end_point = np.array([size, 0, z])

            start_2d = project_3d_to_2d(start_point, camera)
            end_2d = project_3d_to_2d(end_point, camera)

            if start_2d and end_2d:
                renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))

        # Create grid lines parallel to Z axis
        for x in range(-size, size + spacing, spacing):
            start_point = np.array([x, 0, -size])
            end_point = np.array([x, 0, size])

            start_2d = project_3d_to_2d(start_point, camera)
            end_2d = project_3d_to_2d(end_point, camera)

            if start_2d and end_2d:
                renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))

        # Draw center lines slightly brighter
        renderer.color = sdl2.ext.Color(120, 120, 120, 255)  # Lighter gray

        # Center line along X axis
        start_2d = project_3d_to_2d(np.array([-size, 0, 0]), camera)
        end_2d = project_3d_to_2d(np.array([size, 0, 0]), camera)
        if start_2d and end_2d:
            renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))

        # Center line along Z axis
        start_2d = project_3d_to_2d(np.array([0, 0, -size]), camera)
        end_2d = project_3d_to_2d(np.array([0, 0, size]), camera)
        if start_2d and end_2d:
            renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))


def draw_cube(renderer, obj_data, camera):
    """Draw a single cube at a given position with given scale"""
    # Create vertices for this cube
    vertices = create_cube_vertices(obj_data["scale"])

    # Translate vertices to cube position
    translated_vertices = vertices + np.array(obj_data["pos"])

    # Project all vertices to 2D
    projected_vertices = []
    for vertex in translated_vertices:
        point_2d = project_3d_to_2d(vertex, camera)
        projected_vertices.append(point_2d)

    # Draw triangles (filled faces)
    if RENDER_TRIANGLES:
        for triangle in cube_geometry["triangles"]:
            # Get the 3D vertices for this triangle
            v1 = translated_vertices[triangle["vertices"][0]]
            v2 = translated_vertices[triangle["vertices"][1]]
            v3 = translated_vertices[triangle["vertices"][2]]

            # Project to 2D
            p1 = project_3d_to_2d(v1, camera)
            p2 = project_3d_to_2d(v2, camera)
            p3 = project_3d_to_2d(v3, camera)

            # Only render if all vertices are visible
            if p1 and p2 and p3:
                # Apply object color tint to triangle color
                tinted_color = apply_color_tint(triangle["color"], obj_data["color"])
                render_triangle(renderer, p1, p2, p3, tinted_color)

    # Draw wireframe edges
    if RENDER_WIREFRAME:
        renderer.color = sdl2.ext.Color(200, 200, 200, 255)  # Light gray for edges
        for edge in cube_geometry["edges"]:
            start_vertex = projected_vertices[edge[0]]
            end_vertex = projected_vertices[edge[1]]

            if start_vertex and end_vertex:
                renderer.draw_line(
                    (start_vertex[0], start_vertex[1], end_vertex[0], end_vertex[1])
                )


def render_scene(renderer, camera, scene_objects):
    """Render all objects in the scene based on their type"""
    for obj in scene_objects:
        if obj["type"] == "ground_plane":
            draw_ground_plane(renderer, camera, obj["size"], obj["spacing"])
        elif obj["type"] == "axes":
            draw_axes(renderer, camera)
        elif obj["type"] == "cube":
            draw_cube(renderer, obj, camera)
        elif obj["type"] == "vertical_plane":
            draw_vertical_plane(renderer, obj, camera)


def draw_vertical_plane(renderer, obj_data, camera):
    """Draw a vertical plane"""
    if RENDER_TRIANGLES:
        triangles = create_vertical_plane_triangles(obj_data["size"])
        for triangle in triangles:
            # Translate vertices to plane position
            translated_vertices = []
            for vertex in triangle["vertices"]:
                translated_vertex = [
                    vertex[0] + obj_data["pos"][0],
                    vertex[1] + obj_data["pos"][1],
                    vertex[2] + obj_data["pos"][2],
                ]
                translated_vertices.append(translated_vertex)

            # Project triangle vertices to 2D with depth
            p1_result = project_3d_to_2d(translated_vertices[0], camera)
            p2_result = project_3d_to_2d(translated_vertices[1], camera)
            p3_result = project_3d_to_2d(translated_vertices[2], camera)

            # Only render if all vertices are visible
            if p1_result and p2_result and p3_result:
                # Extract 2D positions and depths
                p1, z1 = (p1_result[0], p1_result[1]), p1_result[2]
                p2, z2 = (p2_result[0], p2_result[1]), p2_result[2]
                p3, z3 = (p3_result[0], p3_result[1]), p3_result[2]

                # Apply object color tint to triangle color
                tinted_color = apply_color_tint(triangle["color"], obj_data["color"])
                render_triangle(renderer, p1, p2, p3, tinted_color, z1, z2, z3)


def draw_axes(renderer, camera):
    """Draw the 3D coordinate axes"""
    origin = np.array([0, 0, 0])
    axis_length = axes_geometry["length"]

    # Define axis endpoints
    x_axis = np.array([axis_length, 0, 0])
    y_axis = np.array([0, axis_length, 0])
    z_axis = np.array([0, 0, axis_length])

    # Project points
    origin_2d = project_3d_to_2d(origin, camera)
    x_axis_2d = project_3d_to_2d(x_axis, camera)
    y_axis_2d = project_3d_to_2d(y_axis, camera)
    z_axis_2d = project_3d_to_2d(z_axis, camera)

    if origin_2d:
        # X axis
        if x_axis_2d:
            color = axes_geometry["colors"]["x"]
            renderer.color = sdl2.ext.Color(color[0], color[1], color[2], 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], x_axis_2d[0], x_axis_2d[1]))
            draw_circle_filled(renderer, x_axis_2d[0], x_axis_2d[1], 3)

        # Y axis
        if y_axis_2d:
            color = axes_geometry["colors"]["y"]
            renderer.color = sdl2.ext.Color(color[0], color[1], color[2], 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], y_axis_2d[0], y_axis_2d[1]))
            draw_circle_filled(renderer, y_axis_2d[0], y_axis_2d[1], 3)

        # Z axis
        if z_axis_2d:
            color = axes_geometry["colors"]["z"]
            renderer.color = sdl2.ext.Color(color[0], color[1], color[2], 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], z_axis_2d[0], z_axis_2d[1]))
            draw_circle_filled(renderer, z_axis_2d[0], z_axis_2d[1], 3)


# Rendering options
RENDER_WIREFRAME = True  # Set to False to disable wireframe edges
RENDER_TRIANGLES = True  # Set to False to disable filled triangles
USE_Z_BUFFER = True  # True for z-buffered rendering, False for simple overlay

# Projection method selection
USE_MATRIX_PROJECTION = True  # True for matrix method, False for direct method

# Colors
BLACK = sdl2.ext.Color(0, 0, 0, 255)


def setup_camera_and_projection():
    """
    RENDER STEP 3: Create camera and configure projection settings
    This sets up the viewpoint and projection method - will work with both CPU and GPU rendering
    """
    print("=== RENDER STEP 3: Setting up camera and projection ===")

    # Create camera positioned above ground, looking at scene center
    camera = Camera(position=[400, 200, 800], target=[0, 0, 0], focal_length=600)

    # Orbit parameters for camera animation
    orbit_params = {
        "radius": 800,  # Distance from center
        "height": 200,  # Y position ABOVE ground
        "speed": 0.5,  # Rotation speed
    }

    print(f"✓ Camera created at position: {camera.position}")
    print(f"✓ Camera target: {camera.target}")
    print(f"✓ Camera focal length: {camera.focal_length}")
    print(
        f"✓ Orbit parameters: radius={orbit_params['radius']}, height={orbit_params['height']}"
    )

    return camera, orbit_params


# Projection method selection based on configuration
def project_3d_to_2d(point, camera, width=WIDTH, height=HEIGHT):
    if USE_MATRIX_PROJECTION:
        return project_3d_to_2d_via_matrix(point, camera, width, height)
    else:
        return project_3d_to_2d_direct(point, camera, width, height)


# Triangle rendering wrapper - handles z-buffer toggle
def render_triangle(renderer, p1, p2, p3, color, z1=None, z2=None, z3=None):
    """Unified triangle rendering that automatically chooses z-buffered or regular rendering"""
    if USE_Z_BUFFER and z1 is not None and z2 is not None and z3 is not None:
        # Extract 2D coordinates if we have 3D points
        if len(p1) == 3:
            p1_2d, p2_2d, p3_2d = (p1[0], p1[1]), (p2[0], p2[1]), (p3[0], p3[1])
            z1, z2, z3 = p1[2], p2[2], p3[2]
        else:
            p1_2d, p2_2d, p3_2d = p1, p2, p3
        rasterize_triangle_with_depth(renderer, p1_2d, p2_2d, p3_2d, z1, z2, z3, color)
    else:
        # Regular rasterization (no depth testing)
        if len(p1) == 3:
            p1_2d, p2_2d, p3_2d = (p1[0], p1[1]), (p2[0], p2[1]), (p3[0], p3[1])
        else:
            p1_2d, p2_2d, p3_2d = p1, p2, p3
        rasterize_triangle(renderer, p1_2d, p2_2d, p3_2d, color)


def run_main_loop(window, renderer, camera, orbit_params, scene_objects):
    """
    RENDER STEP 4: Main rendering loop
    This handles input, animation, and frame rendering - will work with both CPU and GPU rendering
    """
    print("=== RENDER STEP 4: Starting main rendering loop ===")
    print("Controls: Close window to exit")
    print("Camera will orbit around the scene")

    running = True
    event = sdl2.SDL_Event()
    start_time = time.time()
    fps_counter = FPSCounter()

    # Colors
    BLACK = sdl2.ext.Color(0, 0, 0, 255)

    # X axis (Red): Left ← → Right (negative X is left, positive X is right)
    # Y axis (Green): Down ← → Up (negative Y is down, positive Y is up)
    # Z axis (Blue): Away ← → Toward Camera (negative Z is away/back, positive Z is toward/front)

    while running:
        # Handle input events
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False

        # Update FPS counter
        if fps_counter.update():
            logging.info("3D Scene - FPS: %.1f", fps_counter.get_fps())

        # Calculate current time and animate camera
        current_time = time.time() - start_time
        orbit_angle = current_time * orbit_params["speed"]
        camera.update_orbit(orbit_angle, orbit_params["radius"], orbit_params["height"])

        # Clear screen and z-buffer (if using z-buffer)
        if USE_Z_BUFFER:
            clear_z_buffer()
        renderer.color = BLACK
        renderer.clear()

        # Render all scene objects (CPU rasterization - will become GPU draw calls)
        render_scene(renderer, camera, scene_objects)

        # Present the frame
        renderer.present()

        # Control frame rate (roughly 60 FPS)
        sdl2.SDL_Delay(16)

    print("✓ Main loop finished")


def cleanup():
    """Clean up SDL2 resources"""
    print("=== Cleaning up resources ===")
    sdl2.ext.quit()
    print("✓ SDL2 resources cleaned up")


def main():
    """
    Main function demonstrating the 4-step CPU rendering pipeline:
    1. Setup display and rendering context
    2. Create 3D scene geometry and objects
    3. Setup camera and projection settings
    4. Run main rendering loop

    This structure will make it easy to transition to OpenGL later
    """
    print("=== 3D SCENE RENDERER - CPU PIPELINE DEMO ===")
    print("This demonstrates the 4 essential steps for 3D rendering")
    print("(Structure designed to easily transition to OpenGL/GPU rendering)\n")

    try:
        # Step 1: Create display surface and rendering context
        window, renderer, width, height = setup_display_and_renderer()

        # Step 2: Create 3D scene with objects to render
        scene_objects = create_scene_objects()

        # Step 3: Setup camera and configure projection
        camera, orbit_params = setup_camera_and_projection()

        # Step 4: Run the main rendering loop
        run_main_loop(window, renderer, camera, orbit_params, scene_objects)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always clean up resources
        cleanup()


if __name__ == "__main__":
    main()
