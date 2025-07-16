This is a repo to learn the math behind rendering 2d/3d scenes.

![](./manual-render.gif)

What you are seeing here is a 2d "scene" where we have four 2d vectors (points)
in space. The key observation is that we are working in our world, whatever
that is. And we have units. Our objects will be created by just adding
points/vectors (and other things like lines) in our world. 

For example, what you are looking at has:

```c
    Point points[] = {
        {0, 0}, {2, 0}, {2, 2}, {0, 2}
    };

    Line lines[] = {
        {{0, 0}, {2, 0}},
        {{2, 0}, {2, 2}},
        {{2, 2}, {0, 2}},
        {{0, 2}, {0, 0}}
    };
```

Now, what we are saying here is that our world has a vector at (0,0). Zero units in x and 
zero units in y. Those units can be whatever we want. It could be gps coordinates to define
our objects in our "real" world.

The next step to build a solid mental model is the camera. The camera looks at our world, 
but the camera has a viewfinder/lcd screen that is limited in space. Our world is limitless.
It is infiniteWhat you are seeing here is a 2d "scene" where we have four 2d vectors (points)
in space. The key observation is that we are working in our world, whatever
that is. And we have units. Our objects will be created by just adding
points/vectors (and other things like lines) in our world. 

.

So we are trying to answer:

“Where should I draw that on a 800×600 screen so it appears in the right place,
given the camera position and zoom?”

Our camera defines:
1. center_x, center_y: What world point is the center of the screen.
2. zoom: how many pixels per world unit. 

We need to map between our world to the camera. For that we have:

```c
Point world_to_screen(float world_x, float world_y, Camera* cam, int screen_width, int screen_height) {
    Point screen_point;
    screen_point.x = (int)((world_x - cam->center_x) * cam->zoom + screen_width / 2);
    screen_point.y = (int)((world_y - cam->center_y) * cam->zoom + screen_height / 2);
    return screen_point;
}
```

Let's unpack that:

### 1. Translate world so the camera is at (0,0)

We want the camera to behave like a viewer at the origin looking around. For that we answer: 
How far is the current vector/point from where the camera is looking at. 

```
# example 1
wx = 1.5, wy = 0.5
camera.center = (1.0, 1.0)

tx = 1.5 - 1.0 = 0.5
ty = 0.5 - 1.0 = -0.5

Point (1.5, 0.5) is (0.5, -0,5) units from the camera view point (1.0, 1.0).

# example 2
wx = 0, wy = 0
camera.center = (2, 2)

tx = 0 - 2 = -2
ty = 0 - 2 = -2

Point (0, 0) is (-2, -2) units from the camera view point (2,2).
```

Insight: there is not concept of center in our world, just locations. 
We do have a center in our screen/camera view.


### 2. Scale relative position into pixels

That's an easy one (For 2D!). We just need to multiple by our zoom (factor).

### 3. Move to the center of the screen

We want the camera’s focus point (camera.center) to be drawn at the center of the screen.

So shift everything by (screen_width / 2, screen_height / 2).

## The mental model

To build more intuition I think about this: Imagine that our world is a piece
of infinite paper. We  start drawing things there (points for now).  This is
your world, it extends forever in all directions.

Now we have a piece of paper with a hole in a  rectangle shape. It is looking
parallel at the infinite piece of paper. The size of the rectangle is our
screen and it has a size. Now, the piece of paper has a distance from the
infinite paper. That is the zoom. 

## Future work:

We are only doing a few "transformations", we could also: rotate, project (tilt the window).

Our world (in this example not the real one :)) is a flat infinite plane. Object sizes never
changes because the distance to our camera is the same. Which is fine for now. We can still
have tons of fun. 

We are applying the math in a point by point, coordinate by coordinate. Linear algebra and
matrix multiplication allows us to perform this computations in a more efficient way.


