#!./.venv/bin/python

import sdl2
import sdl2.ext
import numpy as np
import math
import ctypes

# Initialize SDL2
sdl2.ext.init()

# Create window and renderer
WIDTH, HEIGHT = 800, 600
X = 3025
Y = 48
window = sdl2.ext.Window("Simple 3D Cube - SDL2", size=(WIDTH, HEIGHT))
sdl2.SDL_SetWindowPosition(window.window, X, Y)

window.show()

# Create a renderer for drawing
renderer = sdl2.ext.Renderer(window)

# Define a cube (8 vertices)
cube_vertices = np.array([
    [-1, -1, -1],  # 0: back bottom left
    [ 1, -1, -1],  # 1: back bottom right
    [ 1,  1, -1],  # 2: back top right
    [-1,  1, -1],  # 3: back top left
    [-1, -1,  1],  # 4: front bottom left
    [ 1, -1,  1],  # 5: front bottom right
    [ 1,  1,  1],  # 6: front top right
    [-1,  1,  1],  # 7: front top left
]) * 50  # Scale up the cube

# Define edges (which vertices to connect)
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),  # back face
    (4, 5), (5, 6), (6, 7), (7, 4),  # front face
    (0, 4), (1, 5), (2, 6), (3, 7),  # connecting edges
]

# Define faces with different colors
faces = [
    {"vertices": [0, 1, 2, 3], "color": (100, 100, 255), "name": "back"},    # blue
    {"vertices": [4, 5, 6, 7], "color": (255, 100, 100), "name": "front"},  # red
    {"vertices": [0, 1, 5, 4], "color": (100, 255, 100), "name": "bottom"}, # green
    {"vertices": [2, 3, 7, 6], "color": (255, 255, 100), "name": "top"},    # yellow
    {"vertices": [0, 3, 7, 4], "color": (255, 100, 255), "name": "left"},   # magenta
    {"vertices": [1, 2, 6, 5], "color": (100, 255, 255), "name": "right"},  # cyan
]

# Camera settings
camera_pos = np.array([0, 0, -550])  # Camera position
camera_yaw = math.radians(0)         # Facing +Z
camera_pitch = math.radians(0)       # Level
focal_length = 500                   # Zoom

def rotate_y(vertices, angle):
    """Rotate vertices around Y axis"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    rotation_matrix = np.array([
        [cos_a,  0, sin_a],
        [0,      1, 0],
        [-sin_a, 0, cos_a]
    ])
    return vertices @ rotation_matrix.T

def rotate_x(vertices, angle):
    """Rotate vertices around X axis"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    rotation_matrix = np.array([
        [1, 0,      0],
        [0, cos_a, -sin_a],
        [0, sin_a,  cos_a]
    ])
    return vertices @ rotation_matrix.T

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

def project_3d_to_2d_simple(vertex_3d, camera_pos, focal_length):
    """Project a 3D point to 2D screen coordinates"""
    # Translate vertex relative to camera
    relative_pos = vertex_3d - camera_pos

    # Simple perspective projection
    # We divide X and Y by Z to create perspective effect
    if relative_pos[2] > 0:  # Only project if in front of camera
        x_2d = (focal_length * relative_pos[0]) / relative_pos[2]
        y_2d = (focal_length * relative_pos[1]) / relative_pos[2]

        # Convert to screen coordinates (center of screen is origin)
        screen_x = int(x_2d + WIDTH / 2)
        screen_y = int(y_2d + HEIGHT / 2)

        return (screen_x, screen_y)
    return None

def project_3d_to_2d(point, camera_pos, target_pos, focal_length):
    """
    Project 3D point to 2D, with camera looking at target_pos
    """
    # Step 1: Create camera coordinate system
    # This vector tells us how many units (x,y,z) to move to get from the camera
    # to the center of the object we are looking at
    # Normalize to so our vector is size 1
    forward = normalize(np.array(target_pos) - np.array(camera_pos))
    world_up = np.array([0, 1, 0])
    # I know what is up (in world space) and what is forward, let's find what is right
    right = normalize(cross(world_up, forward))
    # And now we get the
    up = cross(forward, right)
    # So what do we have?
    # We now have a complete orthonormal coordinate system centered at the camera position, 
    # with three perpendicular unit vectors that define the camera's personal orientation in space.
    # This is kind of you 
    
    # Step 2: Transform point to camera space
    # the vector that points from the camera position to the point we want to project.
    relative = np.array(point) - np.array(camera_pos)
    # Now use the dot product to compute:
    # Transform the point from world coordinates to camera coordinates
    # Analogy: think about the monitor you are looking at. That monitor is at whatever coordinates
    # in world space (earth space) but I am looking at it with my eyes (camera). For the camera, 
    # that object is now in its coordinate system.
    x_cam = dot(relative, right)
    y_cam = dot(relative, up)
    z_cam = dot(relative, forward)
    
    # Step 3: Perspective projection (only if point is in front of camera)
    # Notice we could use a orthographic projection, in that case we wouldn't have to 
    # perform this computations to adjust the x,y values based on the focal_length. 
    # Every object would appear at the same distance. We would not use the depth of the object. 
    # But we are using a Perspective projection so we have to account for that
    if z_cam > 0.1:  # Small epsilon to avoid division by zero
        x_2d = (focal_length * x_cam) / z_cam
        y_2d = (focal_length * y_cam) / z_cam
        # now, If I have a point in (0,0) that will have to go to 
        # (0+400, 0+300), which is (0+WIDTH/2, 0+HEIGHT/2).
        return (int(x_2d + WIDTH/2), int(y_2d + HEIGHT/2))
    return None


def draw_circle_filled(renderer, x, y, radius):
    """Draw a filled circle using SDL2"""
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx*dx + dy*dy <= radius*radius:
                renderer.draw_point((x + dx, y + dy))

def draw_face_centers(renderer, vertices, camera_pos, target_pos, focal_length):
    """Draw colored dots at the center of each face"""
    for face in faces:
        # Calculate face center
        face_vertices = [vertices[i] for i in face["vertices"]]
        center = np.mean(face_vertices, axis=0)

        # Project to 2D
        center_2d = project_3d_to_2d(center, camera_pos, target_pos, focal_length)

        if center_2d:
            # Set color for this face
            color = face["color"]
            renderer.color = sdl2.ext.Color(color[0], color[1], color[2], 255)
            # Draw a larger circle for the face center
            draw_circle_filled(renderer, int(center_2d[0]), int(center_2d[1]), 8)

def draw_axes(renderer, camera_pos, target_pos, focal_length):
    """Draw the 3D coordinate axes"""
    origin = np.array([0, 0, 0])
    axis_length = 400

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
            # Draw small arrow head
            draw_circle_filled(renderer, x_axis_2d[0], x_axis_2d[1], 3)

        # Y axis - Green
        if y_axis_2d:
            renderer.color = sdl2.ext.Color(0, 255, 0, 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], y_axis_2d[0], y_axis_2d[1]))
            # Draw small arrow head
            draw_circle_filled(renderer, y_axis_2d[0], y_axis_2d[1], 3)

        # Z axis - Blue
        if z_axis_2d:
            renderer.color = sdl2.ext.Color(0, 0, 255, 255)
            renderer.draw_line((origin_2d[0], origin_2d[1], z_axis_2d[0], z_axis_2d[1]))
            # Draw small arrow head
            draw_circle_filled(renderer, z_axis_2d[0], z_axis_2d[1], 3)

# Colors
WHITE = sdl2.ext.Color(255, 255, 255, 255)
RED = sdl2.ext.Color(255, 100, 100, 255)
BLACK = sdl2.ext.Color(0, 0, 0, 255)

# Main loop
running = True
angle_y = 0
angle_x = 0
event = sdl2.SDL_Event()

theta = 0
phi = 0
#camera_movement_method="circle"
camera_movement_method="sphere"

while running:
    # Handle events
    while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
        if event.type == sdl2.SDL_QUIT:
            running = False

    # Clear screen
    renderer.color = BLACK
    renderer.clear()

    if camera_movement_method == "circle":
        # Update rotation angles  
        angle_y += 0.01
        angle_x += 0.005

        # Move camera in a circle around the cube
        camera_angle = angle_y * 0.5  # Slower than cube rotation
        camera_radius = 550
        camera_pos = np.array([
            camera_radius * math.sin(camera_angle),  # X position
            0,                                       # Y position (level)
            camera_radius * math.cos(camera_angle)   # Z position
        ])

    if camera_movement_method == "sphere":
        # Two angles control the sphere
        theta += 0.01    # Horizontal rotation (azimuth)
        phi += 0.005     # Vertical rotation (elevation)
        radius = 550

        camera_pos = np.array([
            radius * math.sin(phi) * math.cos(theta),  # X
            radius * math.cos(phi),                    # Y  
            radius * math.sin(phi) * math.sin(theta)   # Z
        ])


    # Draw the coordinate axes
    cube_center = np.array([0, 0, 0])
    draw_axes(renderer, camera_pos, cube_center, focal_length)

    # Rotate the cube
    #rotated_vertices = rotate_y(cube_vertices, angle_y)
    #rotated_vertices = rotate_x(rotated_vertices, angle_x)

    # Project all vertices to 2D (camera always looks at cube center)
    projected_vertices = []
    for vertex in cube_vertices:
        point_2d = project_3d_to_2d(vertex, camera_pos, cube_center, focal_length)
        projected_vertices.append(point_2d)

    # Draw edges
    renderer.color = WHITE
    for edge in edges:
        start_vertex = projected_vertices[edge[0]]
        end_vertex = projected_vertices[edge[1]]

        # Only draw if both vertices are visible
        if start_vertex and end_vertex:
            renderer.draw_line((start_vertex[0], start_vertex[1],
                               end_vertex[0], end_vertex[1]))

    # Draw vertices as points
    renderer.color = RED
    for vertex_2d in projected_vertices:
        if vertex_2d:
            draw_circle_filled(renderer, vertex_2d[0], vertex_2d[1], 4)

    # Draw face centers with colors
    draw_face_centers(renderer, cube_vertices, camera_pos, cube_center, focal_length)

    # Present the frame
    renderer.present()

    # Control frame rate (roughly 60 FPS)
    sdl2.SDL_Delay(16)

# Cleanup
sdl2.ext.quit()
