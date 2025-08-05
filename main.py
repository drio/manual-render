#!./.venv/bin/python

import ctypes
import math

import numpy as np
import sdl2
import sdl2.ext

# Initialize SDL2
sdl2.ext.init()

# Create window and renderer
WIDTH, HEIGHT = 800, 600
X = 3025
Y = 48
window = sdl2.ext.Window("3D Scene with Ground Plane - SDL2", size=(WIDTH, HEIGHT))
sdl2.SDL_SetWindowPosition(window.window, X, Y)

window.show()

# Create a renderer for drawing
renderer = sdl2.ext.Renderer(window)


def create_cube_vertices(scale=50):
    """Create cube vertices with given scale"""
    return (
        np.array(
            [
                [-1, -1, -1],  # 0: back bottom left
                [1, -1, -1],  # 1: back bottom right
                [1, 1, -1],  # 2: back top right
                [-1, 1, -1],  # 3: back top left
                [-1, -1, 1],  # 4: front bottom left
                [1, -1, 1],  # 5: front bottom right
                [1, 1, 1],  # 6: front top right
                [-1, 1, 1],  # 7: front top left
            ]
        )
        * scale
    )


# Define edges (which vertices to connect)
cube_edges = [
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
]

# Define faces with different colors
cube_faces = [
    # {"vertices": [0, 1, 2, 3], "color": (100, 100, 255), "name": "back"},  # blue
    # {"vertices": [4, 5, 6, 7], "color": (255, 100, 100), "name": "front"},  # red
    # {"vertices": [0, 1, 5, 4], "color": (100, 255, 100), "name": "bottom"},  # green
    # {"vertices": [2, 3, 7, 6], "color": (255, 255, 100), "name": "top"},  # yellow
    # {"vertices": [0, 3, 7, 4], "color": (255, 100, 255), "name": "left"},  # magenta
    # {"vertices": [1, 2, 6, 5], "color": (100, 255, 255), "name": "right"},  # cyan
]

# Create multiple cubes with different sizes and positions
cubes = [
    {"pos": [0, 25, 0], "scale": 50, "color_tint": (255, 255, 255), "name": "center"},
    {"pos": [120, 40, 80], "scale": 80, "color_tint": (255, 200, 200), "name": "large"},
    {
        "pos": [-100, 15, -50],
        "scale": 30,
        "color_tint": (200, 255, 200),
        "name": "small",
    },
    {"pos": [80, 60, -120], "scale": 120, "color_tint": (200, 200, 255), "name": "big"},
    {
        "pos": [-80, 20, 100],
        "scale": 40,
        "color_tint": (255, 255, 200),
        "name": "medium",
    },
    {"pos": [0, 10, -200], "scale": 20, "color_tint": (255, 200, 255), "name": "tiny"},
]

# Camera settings
camera_pos = np.array([0, 0, -550])  # Camera position
focal_length = 500  # Zoom


def normalize(vector):
    """Normalize a vector to unit length"""
    v = np.array(vector)
    length = np.linalg.norm(v)
    if length == 0:
        return v
    return v / length


def cross(a, b):
    """Calculate cross product of two 3D vectors"""
    return np.cross(a, b)


def dot(a, b):
    """Calculate dot product of two vectors"""
    return np.dot(a, b)


def project_3d_to_2d(point, camera_pos, target_pos, focal_length):
    """Project 3D point to 2D, with camera looking at target_pos"""
    # Create camera coordinate system
    forward = normalize(np.array(target_pos) - np.array(camera_pos))
    world_up = np.array([0, 1, 0])
    right = normalize(cross(world_up, forward))
    up = cross(forward, right)

    # Transform point to camera space
    relative = np.array(point) - np.array(camera_pos)
    x_cam = dot(relative, right)
    y_cam = dot(relative, up)
    z_cam = dot(relative, forward)

    # Perspective projection
    if z_cam > 0.1:  # Small epsilon to avoid division by zero
        x_2d = (focal_length * x_cam) / z_cam
        y_2d = (focal_length * y_cam) / z_cam
        return (int(x_2d + WIDTH / 2), int(y_2d + HEIGHT / 2))
    return None


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


def draw_ground_plane(
    renderer, camera_pos, target_pos, focal_length, size=400, spacing=50
):
    """Draw a grid ground plane"""
    renderer.color = sdl2.ext.Color(80, 80, 80, 255)  # Dark gray

    # Create grid lines parallel to X axis
    for z in range(-size, size + spacing, spacing):
        start_point = np.array([-size, 0, z])
        end_point = np.array([size, 0, z])

        start_2d = project_3d_to_2d(start_point, camera_pos, target_pos, focal_length)
        end_2d = project_3d_to_2d(end_point, camera_pos, target_pos, focal_length)

        if start_2d and end_2d:
            renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))

    # Create grid lines parallel to Z axis
    for x in range(-size, size + spacing, spacing):
        start_point = np.array([x, 0, -size])
        end_point = np.array([x, 0, size])

        start_2d = project_3d_to_2d(start_point, camera_pos, target_pos, focal_length)
        end_2d = project_3d_to_2d(end_point, camera_pos, target_pos, focal_length)

        if start_2d and end_2d:
            renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))

    # Draw center lines slightly brighter
    renderer.color = sdl2.ext.Color(120, 120, 120, 255)  # Lighter gray

    # Center line along X axis
    start_2d = project_3d_to_2d(
        np.array([-size, 0, 0]), camera_pos, target_pos, focal_length
    )
    end_2d = project_3d_to_2d(
        np.array([size, 0, 0]), camera_pos, target_pos, focal_length
    )
    if start_2d and end_2d:
        renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))

    # Center line along Z axis
    start_2d = project_3d_to_2d(
        np.array([0, 0, -size]), camera_pos, target_pos, focal_length
    )
    end_2d = project_3d_to_2d(
        np.array([0, 0, size]), camera_pos, target_pos, focal_length
    )
    if start_2d and end_2d:
        renderer.draw_line((start_2d[0], start_2d[1], end_2d[0], end_2d[1]))


def draw_cube(renderer, cube_data, camera_pos, target_pos, focal_length):
    """Draw a single cube at a given position with given scale"""
    # Create vertices for this cube
    vertices = create_cube_vertices(cube_data["scale"])

    # Translate vertices to cube position
    translated_vertices = vertices + np.array(cube_data["pos"])

    # Project all vertices to 2D
    projected_vertices = []
    for vertex in translated_vertices:
        point_2d = project_3d_to_2d(vertex, camera_pos, target_pos, focal_length)
        projected_vertices.append(point_2d)

    # Draw edges
    renderer.color = sdl2.ext.Color(200, 200, 200, 255)  # Light gray for edges
    for edge in cube_edges:
        start_vertex = projected_vertices[edge[0]]
        end_vertex = projected_vertices[edge[1]]

        if start_vertex and end_vertex:
            renderer.draw_line(
                (start_vertex[0], start_vertex[1], end_vertex[0], end_vertex[1])
            )

    # Draw face centers with tinted colors
    for face in cube_faces:
        # Calculate face center
        face_vertices = [translated_vertices[i] for i in face["vertices"]]
        center = np.mean(face_vertices, axis=0)

        # Project to 2D
        center_2d = project_3d_to_2d(center, camera_pos, target_pos, focal_length)

        if center_2d:
            # Apply color tint
            tinted_color = apply_color_tint(face["color"], cube_data["color_tint"])
            renderer.color = sdl2.ext.Color(
                tinted_color[0], tinted_color[1], tinted_color[2], 255
            )

            # Scale dot size with cube size
            dot_size = max(3, int(cube_data["scale"] / 15))
            draw_circle_filled(renderer, int(center_2d[0]), int(center_2d[1]), dot_size)


def draw_axes(renderer, camera_pos, target_pos, focal_length):
    """Draw the 3D coordinate axes"""
    origin = np.array([0, 0, 0])
    axis_length = 100  # Shorter axes so they don't dominate

    # Define axis endpoints
    x_axis = np.array([axis_length, 0, 0])
    y_axis = np.array([0, axis_length, 0])
    z_axis = np.array([0, 0, axis_length])

    # Project points
    origin_2d = project_3d_to_2d(origin, camera_pos, target_pos, focal_length)
    x_axis_2d = project_3d_to_2d(x_axis, camera_pos, target_pos, focal_length)
    y_axis_2d = project_3d_to_2d(y_axis, camera_pos, target_pos, focal_length)
    z_axis_2d = project_3d_to_2d(z_axis, camera_pos, target_pos, focal_length)

    if origin_2d:
        # X axis - Red
        if x_axis_2d:
            renderer.color = sdl2.ext.Color(255, 0, 0, 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], x_axis_2d[0], x_axis_2d[1]))
            draw_circle_filled(renderer, x_axis_2d[0], x_axis_2d[1], 3)

        # Y axis - Green
        if y_axis_2d:
            renderer.color = sdl2.ext.Color(0, 255, 0, 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], y_axis_2d[0], y_axis_2d[1]))
            draw_circle_filled(renderer, y_axis_2d[0], y_axis_2d[1], 3)

        # Z axis - Blue
        if z_axis_2d:
            renderer.color = sdl2.ext.Color(0, 0, 255, 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], z_axis_2d[0], z_axis_2d[1]))
            draw_circle_filled(renderer, z_axis_2d[0], z_axis_2d[1], 3)


# Colors
BLACK = sdl2.ext.Color(0, 0, 0, 255)

# Main loop
running = True
event = sdl2.SDL_Event()

while running:
    # Handle events
    while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
        if event.type == sdl2.SDL_QUIT:
            running = False

    # Clear screen
    renderer.color = BLACK
    renderer.clear()

    camera_pos = np.array([-500, -300, 500])

    # Always look at the center of our scene
    scene_center = np.array([0, 50, 0])  # Look slightly up from ground

    # Draw the ground plane first (so it appears behind everything)
    draw_ground_plane(renderer, camera_pos, scene_center, focal_length)

    # Draw coordinate axes
    draw_axes(renderer, camera_pos, scene_center, focal_length)

    # Draw all cubes
    for cube in cubes:
        draw_cube(renderer, cube, camera_pos, scene_center, focal_length)

    # Present the frame
    renderer.present()

    # Control frame rate (roughly 60 FPS)
    sdl2.SDL_Delay(16)

# Cleanup
sdl2.ext.quit()
