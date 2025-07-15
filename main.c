#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

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

// Transform world coordinates to screen coordinates
Point world_to_screen(float world_x, float world_y, Camera* cam) {
    // For now, just pass through unchanged (no transformation)
    Point screen_point;
    screen_point.x = (int)world_x;
    screen_point.y = (int)world_y;
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
        800, 600,         // width, height
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

    // Initialize camera (neutral - no transformation yet)
    camera.center_x = 300.0f;  // Center of our current square
    camera.center_y = 225.0f;  // Center of our current square  
    camera.zoom = 1.0f;        // No zoom

    // 4 points forming a rectangle
    Point points[] = {
        {200, 150},  // top-left
        {400, 150},  // top-right
        {400, 300},  // bottom-right
        {200, 300}   // bottom-left
    };

    // Lines connecting the points to form a rectangle
    Line lines[] = {
        {{200, 150}, {400, 150}},  // top edge
        {{400, 150}, {400, 300}},  // right edge  
        {{400, 300}, {200, 300}},  // bottom edge
        {{200, 300}, {200, 150}}   // left edge
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
                    Point screen_point = world_to_screen(points[i].x, points[i].y, &camera);
                    XFillArc(display, window, gc, 
                        screen_point.x - 3, screen_point.y - 3, 
                        6, 6, 0, 360 * 64);
                }

                // Draw lines (4 lines forming rectangle)
                for (int i = 0; i < 4; i++) {
                    Point start = world_to_screen(lines[i].start.x, lines[i].start.y, &camera);
                    Point end = world_to_screen(lines[i].end.x, lines[i].end.y, &camera);
                    XDrawLine(display, window, gc,
                        start.x, start.y, end.x, end.y);
                }

                // Draw coordinate axes
                XDrawLine(display, window, gc, 0, 300, 800, 300); // x-axis
                XDrawLine(display, window, gc, 400, 0, 400, 600);  // y-axis

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
