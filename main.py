#!./.venv/bin/python
import ctypes
import math
import time

import numpy as np
import sdl2
import sdl2.ext

from vector_math import cross, dot, normalize

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


class Camera:
    """Simple camera class to group camera-related variables"""

    def __init__(self, position=[-500, -300, 500], target=[0, 50, 0], focal_length=500):
        print(f"camera position= {position}")
        self.position = position
        self.target = target
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
        # Front face (z = 1): vertices [4, 5, 6, 7]
        {"vertices": [4, 5, 6], "color": (255, 100, 100), "name": "front_1"},
        {"vertices": [4, 6, 7], "color": (255, 100, 100), "name": "front_2"},
    ],
}

axes_geometry = {
    "length": 100,
    "colors": {
        "x": (255, 0, 0),  # Red
        "y": (0, 255, 0),  # Green
        "z": (0, 0, 255),  # Blue
    },
}


def create_cube_vertices(scale=50):
    """Create cube vertices with given scale"""
    return np.array(cube_geometry["vertices"]) * scale


# Unified scene objects data structure
scene_objects = [
    {
        "type": "cube",
        "pos": [0, -50, 0],
        "scale": 50,
        "color": (255, 255, 255),
        "name": "center_cube",
    },
    {
        "type": "cube",
        "pos": [250, -80, 100],
        "scale": 80,
        "color": (255, 200, 200),
        "name": "large_cube",
    },
    {
        "type": "cube",
        "pos": [-250, -30, -100],
        "scale": 30,
        "color": (200, 255, 200),
        "name": "small_cube",
    },
    {
        "type": "ground_plane",
        "pos": [0, 0, 0],
        "size": 400,
        "spacing": 50,
        "color": (60, 60, 60),
        "name": "ground",
    },
    {
        "type": "axes",
        "pos": [0, 0, 0],
        "name": "coordinate_axes",
    },
]


def create_view_matrix(camera_pos, target_pos):
    """Create a view matrix that transforms world coordinates to camera coordinates"""
    # Create the camera coordinate system (same as in project_3d_to_2d)
    forward = normalize(np.array(target_pos) - np.array(camera_pos))
    world_up = np.array([0, 1, 0])
    right = normalize(np.cross(world_up, forward))
    up = np.cross(forward, right)

    # The view matrix combines rotation and translation
    # The rotation part uses our right/up/forward vectors as rows
    # The translation part moves the world relative to camera position
    view_matrix = np.array(
        [
            [right[0], right[1], right[2], -np.dot(right, camera_pos)],
            [up[0], up[1], up[2], -np.dot(up, camera_pos)],
            [forward[0], forward[1], forward[2], -np.dot(forward, camera_pos)],
            [0, 0, 0, 1],
        ]
    )

    return view_matrix


def create_projection_matrix(
    focal_length, width, height, near_plane=0.1, far_plane=1000.0
):
    """Create a perspective projection matrix"""
    # Calculate field of view parameters
    aspect_ratio = width / height
    fov_scale_x = focal_length / (width / 2)
    fov_scale_y = focal_length / (height / 2)

    # The projection matrix
    # This matrix transforms camera coordinates to clip coordinates
    projection_matrix = np.array(
        [
            [fov_scale_x, 0, 0, 0],
            [0, fov_scale_y, 0, 0],
            [
                0,
                0,
                -(far_plane + near_plane) / (far_plane - near_plane),
                -2 * far_plane * near_plane / (far_plane - near_plane),
            ],
            [0, 0, -1, 0],
        ]
    )

    return projection_matrix


def create_viewport_matrix(width, height):
    """Create a viewport matrix that converts to screen coordinates"""
    viewport_matrix = np.array(
        [
            [width / 2, 0, 0, width / 2],
            [0, -height / 2, 0, height / 2],  # Negative Y to flip coordinates
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )

    return viewport_matrix


def project_3d_to_2d_via_matrix(point, camera, width=WIDTH, height=HEIGHT):
    """Project 3D point to 2D using matrix transformations"""
    # Create the transformation matrices
    view_matrix = create_view_matrix(camera.position, camera.target)
    projection_matrix = create_projection_matrix(camera.focal_length, width, height)
    viewport_matrix = create_viewport_matrix(width, height)

    # Combine all matrices into a single transformation
    # Matrix multiplication is applied right to left
    mvp_matrix = viewport_matrix @ projection_matrix @ view_matrix

    # Convert point to homogeneous coordinates
    point_homogeneous = np.array([point[0], point[1], point[2], 1.0])

    # Apply the combined transformation
    transformed_point = mvp_matrix @ point_homogeneous

    # Perform perspective division
    if transformed_point[3] != 0:  # Check w coordinate
        screen_x = transformed_point[0] / transformed_point[3]
        screen_y = transformed_point[1] / transformed_point[3]
        screen_z = transformed_point[2] / transformed_point[3]

        # Check if point is visible (in front of camera and w > 0)
        if transformed_point[3] > 0.1:  # Check w coordinate instead of z
            return (int(screen_x), int(screen_y))

    return None


def project_3d_to_2d_direct(point, camera, width=WIDTH, height=HEIGHT):
    """Project 3D point to 2D, with camera looking at target_pos"""
    # Create camera coordinate system
    forward = normalize(np.array(camera.target) - np.array(camera.position))
    world_up = np.array([0, 1, 0])
    right = normalize(cross(world_up, forward))
    up = cross(forward, right)

    # Transform point to camera space
    relative = np.array(point) - np.array(camera.position)
    x_cam = dot(relative, right)
    y_cam = dot(relative, up)
    z_cam = dot(relative, forward)

    # Perspective projection
    if z_cam > 0.1:  # Small epsilon to avoid division by zero
        x_2d = (camera.focal_length * x_cam) / z_cam
        y_2d = (camera.focal_length * y_cam) / z_cam
        return (int(x_2d + width / 2), int(y_2d + height / 2))
    return None


def draw_circle_filled(renderer, x, y, radius):
    """Draw a filled circle using SDL2"""
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                renderer.draw_point((x + dx, y + dy))


def rasterize_triangle(renderer, p1, p2, p3, color):
    """Rasterize a triangle by filling all pixels inside it

    Args:
        renderer: SDL2 renderer
        p1, p2, p3: 2D points as tuples (x, y)
        color: RGB color tuple (r, g, b)
    """
    # Set the color
    renderer.color = sdl2.ext.Color(color[0], color[1], color[2], 255)

    # Find bounding box of the triangle
    min_x = max(0, int(min(p1[0], p2[0], p3[0])))
    max_x = min(WIDTH - 1, int(max(p1[0], p2[0], p3[0])))
    min_y = max(0, int(min(p1[1], p2[1], p3[1])))
    max_y = min(HEIGHT - 1, int(max(p1[1], p2[1], p3[1])))

    # For each pixel in the bounding box, check if it's inside the triangle
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if point_in_triangle(x, y, p1, p2, p3):
                renderer.draw_point((x, y))


def point_in_triangle(px, py, p1, p2, p3):
    """Check if point (px, py) is inside triangle defined by p1, p2, p3

    Uses barycentric coordinates method
    """
    # Get triangle vertices
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    # Calculate barycentric coordinates
    denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    # Check for degenerate triangle
    # A degenerate triangle is what happens when a triangle "collapses" and loses its triangular shape,
    # becoming either a straight line or a single point instead of forming a proper two-dimensional triangle.
    if abs(denom) < 1e-10:
        return False

    a = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom
    b = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom
    c = 1 - a - b

    # Point is inside if all barycentric coordinates are >= 0
    return a >= 0 and b >= 0 and c >= 0


def apply_color_tint(base_color, tint, intensity=0.3):
    """Apply a color tint to a base color"""
    r = int(base_color[0] * (1 - intensity) + tint[0] * intensity)
    g = int(base_color[1] * (1 - intensity) + tint[1] * intensity)
    b = int(base_color[2] * (1 - intensity) + tint[2] * intensity)
    return (min(255, r), min(255, g), min(255, b))


def draw_ground_plane(renderer, camera, size=400, spacing=50):
    """Draw a grid ground plane"""
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
                rasterize_triangle(renderer, p1, p2, p3, tinted_color)

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


def render_scene(renderer, camera):
    """Render all objects in the scene based on their type"""
    for obj in scene_objects:
        if obj["type"] == "ground_plane":
            draw_ground_plane(renderer, camera, obj["size"], obj["spacing"])
        elif obj["type"] == "axes":
            draw_axes(renderer, camera)
        elif obj["type"] == "cube":
            draw_cube(renderer, obj, camera)


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

# Colors
BLACK = sdl2.ext.Color(0, 0, 0, 255)

# Camera positioned above ground, looking at cubes above ground
# camera = Camera(position=[200, -300, 800], target=[0, 0, 0], focal_length=600)
camera = Camera(position=[400, -200, 800], target=[0, 0, 0], focal_length=600)

# Orbit parameters that make sense
orbit_radius = 800  # Distance from center
orbit_height = -200  # Y position ABOVE ground
orbit_speed = 0.5  # Rotation speed


# Choose which projection method to use:
project_3d_to_2d = project_3d_to_2d_direct  # Use direct calculation
# project_3d_to_2d = project_3d_to_2d_via_matrix   # Use matrix method
print(f"Using projection method: {project_3d_to_2d.__name__}")

# Main loop
running = True
event = sdl2.SDL_Event()
start_time = time.time()  # Use real time for smooth animation

# X axis (Red): Left ← → Right (negative X is left, positive X is right)
# Y axis (Green): Down ← → Up (negative Y is down, positive Y is up)
# Z axis (Blue): Away ← → Toward Camera (negative Z is away/back, positive Z is toward/front)
while running:
    # Handle events
    while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
        if event.type == sdl2.SDL_QUIT:
            running = False

    # Calculate current time and camera angle
    current_time = time.time() - start_time
    orbit_angle = current_time * orbit_speed
    # Update camera position to orbit around the scene
    camera.update_orbit(orbit_angle, orbit_radius, orbit_height)

    # Clear screen
    renderer.color = BLACK
    renderer.clear()

    # Render all scene objects
    render_scene(renderer, camera)

    # Present the frame
    renderer.present()

    # Control frame rate (roughly 60 FPS)
    sdl2.SDL_Delay(16)

# Cleanup
sdl2.ext.quit()
