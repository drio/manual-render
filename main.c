#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <unistd.h>

#define SCREEN_WIDTH 800
#define SCREEN_HEIGHT 600

typedef struct {
    int x, y;
} Point;

typedef struct {
    Point start, end;
} Line;

typedef struct {
    float center_x, center_y;  // What world point is at screen center
    float zoom;                // Zoom level (1.0 = normal)
} Camera;

// Given the current position of the camera and zoom level, where on my camera's LCD screen 
// will this world point appear?
Point world_to_screen(float world_x, float world_y, Camera* cam, int screen_width, int screen_height) {
    Point screen_point;
    screen_point.x = (int)
        (
        (world_x - cam->center_x)  // How far is the point (x coordinate) from where I am aiming the camera?
        * cam->zoom                // How big do distances appear? 1 unit spans 100 pixels (assuming zoom = 100)
        + screen_width/2           // Where on my camera/screen does that point goes (x coordinates)
        );
    screen_point.y = (int)((world_y - cam->center_y) * cam->zoom + screen_height/2);
    return screen_point;
}

int main() {
    Display *display;
    Window window;
    XEvent event;
    int screen;
    GC gc;
    Camera camera;

    // Open connection to X server
    display = XOpenDisplay(NULL);
    if (display == NULL) {
        printf("Cannot open display\n");
        return 1;
    }

    screen = DefaultScreen(display);

    // Create window
    window = XCreateSimpleWindow(
        display,
        RootWindow(display, screen),
        10, 10,           // x, y position
        SCREEN_WIDTH, SCREEN_HEIGHT,         // width, height
        1,                // border width
        BlackPixel(display, screen),
        WhitePixel(display, screen)
    );

    // Select events we want to receive
    XSelectInput(display, window, ExposureMask | KeyPressMask | ButtonPressMask);

    // Map (show) the window
    XMapWindow(display, window);

    // Create graphics context
    gc = XCreateGC(display, window, 0, NULL);
    XSetForeground(display, gc, BlackPixel(display, screen));

    // Initialize camera to look at our world square
    camera.center_x = 1.0f;    // Look at center of our 0-2 square
    camera.center_y = 1.0f;    // Look at center of our 0-2 square
    camera.zoom = 100.0f;      // Make 1 world unit = 100 pixels

    // 4 points forming a rectangle in WORLD coordinates
    // Let's say our world square goes from (0,0) to (2,2)
    Point points[] = {
        {0, 0},    // bottom-left in world
        {2, 0},    // bottom-right in world
        {2, 2},    // top-right in world
        {0, 2}     // top-left in world
    };

    // Lines connecting the points to form a rectangle (world coordinates)
    Line lines[] = {
        {{0, 0}, {2, 0}},    // bottom edge
        {{2, 0}, {2, 2}},    // right edge
        {{2, 2}, {0, 2}},    // top edge
        {{0, 2}, {0, 0}}     // left edge
    };

    // Main event loop
    while (1) {
        XNextEvent(display, &event);

        switch (event.type) {
            case Expose:
                // Clear and redraw
                XClearWindow(display, window);

                // Draw points
                for (int i = 0; i < 4; i++) {
                    Point screen_point = world_to_screen(points[i].x, points[i].y, &camera, SCREEN_WIDTH, SCREEN_HEIGHT);
                    XFillArc(display, window, gc,
                        screen_point.x - 3, screen_point.y - 3,
                        6, 6, 0, 360 * 64);
                }

                // Draw lines (4 lines forming rectangle)
                for (int i = 0; i < 4; i++) {
                    Point start = world_to_screen(lines[i].start.x, lines[i].start.y, &camera, SCREEN_WIDTH, SCREEN_HEIGHT);
                    Point end = world_to_screen(lines[i].end.x, lines[i].end.y, &camera, SCREEN_WIDTH, SCREEN_HEIGHT);
                    XDrawLine(display, window, gc,
                        start.x, start.y, end.x, end.y);
                }

                // Draw coordinate axes
                XDrawLine(display, window, gc, 0, SCREEN_HEIGHT/2, SCREEN_WIDTH, SCREEN_HEIGHT/2); // x-axis
                XDrawLine(display, window, gc, SCREEN_WIDTH/2, 0, SCREEN_WIDTH/2, SCREEN_HEIGHT);  // y-axis

                break;

            case KeyPress:
                printf("Key pressed\n");
                goto cleanup;

            case ButtonPress:
                printf("Mouse clicked at (%d, %d)\n",
                    event.xbutton.x, event.xbutton.y);
                break;
        }
    }

cleanup:
    XFreeGC(display, gc);
    XDestroyWindow(display, window);
    XCloseDisplay(display);
    return 0;
}
