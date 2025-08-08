"""
Rasterization functions for the 3D graphics pipeline.

This module contains all the functions related to:
- Triangle rasterization with and without z-buffering
- Point-in-triangle testing
- Barycentric coordinate calculations
"""

import numpy as np
import sdl2.ext

# Global z-buffer - will be initialized by main.py
z_buffer = None


def init_z_buffer(width, height):
    """Initialize the global z-buffer"""
    global z_buffer
    z_buffer = np.full((height, width), float('inf'))


def clear_z_buffer():
    """Clear the z-buffer by filling with infinity"""
    global z_buffer
    if z_buffer is not None:
        z_buffer.fill(float('inf'))


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
    max_x = min(z_buffer.shape[1] - 1, int(max(p1[0], p2[0], p3[0])))
    min_y = max(0, int(min(p1[1], p2[1], p3[1])))
    max_y = min(z_buffer.shape[0] - 1, int(max(p1[1], p2[1], p3[1])))

    # For each pixel in the bounding box, check if it's inside the triangle
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if point_in_triangle(x, y, p1, p2, p3):
                renderer.draw_point((x, y))


def rasterize_triangle_with_depth(renderer, p1, p2, p3, z1, z2, z3, color):
    """Rasterize a triangle with z-buffering

    Args:
        renderer: SDL2 renderer
        p1, p2, p3: 2D points as tuples (x, y)
        z1, z2, z3: Depth values for each vertex
        color: RGB color tuple (r, g, b)
    """
    # Set the color
    renderer.color = sdl2.ext.Color(color[0], color[1], color[2], 255)

    # Find bounding box of the triangle
    min_x = max(0, int(min(p1[0], p2[0], p3[0])))
    max_x = min(z_buffer.shape[1] - 1, int(max(p1[0], p2[0], p3[0])))
    min_y = max(0, int(min(p1[1], p2[1], p3[1])))
    max_y = min(z_buffer.shape[0] - 1, int(max(p1[1], p2[1], p3[1])))

    # For each pixel in the bounding box
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if point_in_triangle(x, y, p1, p2, p3):
                # Interpolate depth using barycentric coordinates
                a, b, c = get_barycentric_coords(x, y, p1, p2, p3)
                pixel_depth = a * z1 + b * z2 + c * z3

                # Depth test
                if pixel_depth < z_buffer[y][x]:  # Note: y first for numpy arrays
                    z_buffer[y][x] = pixel_depth
                    renderer.draw_point((x, y))


def point_in_triangle(px, py, p1, p2, p3):
    """Check if point (px, py) is inside triangle defined by p1, p2, p3

    Given a triangle with vertices A, B, C and a point P, how do we know if P is inside the triangle?

    Uses barycentric coordinates method:
        Barycentric coordinates express any point P as a weighted combination of the triangle's vertices:
        P = a×A + b×B + c×C where a + b + c = 1
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


def get_barycentric_coords(px, py, p1, p2, p3):
    """Calculate barycentric coordinates for interpolation"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(denom) < 1e-10:
        return 0, 0, 0

    a = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom
    b = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom
    c = 1 - a - b
    return a, b, c
