import numpy as np
from vector_math import cross, dot, normalize


def create_view_matrix(camera_pos, target_pos):
    """Create a view matrix that transforms world coordinates to camera coordinates"""
    # Create the camera coordinate system (same as in project_3d_to_2d)
    forward = normalize(np.array(target_pos) - np.array(camera_pos))
    world_up = np.array([0, 1, 0])
    right = normalize(np.cross(forward, world_up))
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


def project_3d_to_2d_via_matrix(point, camera, width, height):
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

        # Check if point is visible (in front of camera)
        # Note: W coordinate can be negative due to coordinate system differences
        if abs(transformed_point[3]) > 0.1:  # Use absolute value
            depth_z = abs(transformed_point[3])  # Convert to positive depth for compatibility
            return (int(screen_x), int(screen_y), depth_z)

    return None


def project_3d_to_2d_direct(point, camera, width, height):
    """Project 3D point to 2D, with camera looking at target_pos"""
    # Create camera coordinate system
    forward = normalize(np.array(camera.target) - np.array(camera.position))
    world_up = np.array([0, 1, 0])
    right = normalize(cross(forward, world_up))
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
        return (int(x_2d + width / 2), int(y_2d + height / 2), z_cam)
    return None