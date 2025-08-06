"""
Vector math utilities for 3D graphics

Contains fundamental vector operations used throughout the 3D pipeline.
"""

import numpy as np


def normalize(vector):
    """Normalize a vector to unit length
    
    Takes any vector and scales it to length 1 while preserving direction.
    Like taking an arrow and making it exactly 1 unit long, but pointing
    the same way. Used for direction vectors in camera calculations.
    
    Example: [3, 4, 0] becomes [0.6, 0.8, 0] (same direction, length=1)
    """
    v = np.array(vector)
    length = np.linalg.norm(v)
    if length == 0:
        return v
    return v / length


def cross(a, b):
    """Calculate cross product of two 3D vectors
    
    Creates a new vector that's perpendicular to both input vectors.
    The result points in the direction your right thumb would point if 
    your fingers curl from vector 'a' to vector 'b'. Used to find the
    "up" and "right" directions for the camera coordinate system.
    
    Example: cross([1,0,0], [0,1,0]) = [0,0,1] (X cross Y = Z)
    """
    return np.cross(a, b)


def dot(a, b):
    """Calculate dot product of two vectors
    
    Measures how much two vectors point in the same direction.
    Result is positive if vectors point roughly same way, negative if 
    opposite ways, zero if perpendicular. Used to project 3D points
    onto camera coordinate axes (how far right/up/forward is a point?).
    
    Example: dot([1,0,0], [1,0,0]) = 1 (same direction)
             dot([1,0,0], [-1,0,0]) = -1 (opposite direction)  
             dot([1,0,0], [0,1,0]) = 0 (perpendicular)
    """
    return np.dot(a, b)