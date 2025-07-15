#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <unistd.h>

typedef struct {
    int x, y;
} Point;

typedef struct {
    Point start, end;
} Line;

int main() {
    Display *display;
    Window window;
    XEvent event;
    int screen;
    GC gc;
    
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
    
    // Some test points and lines
    Point points[] = {
        {100, 100}, {200, 150}, {300, 200}, {400, 100}
    };
    Line lines[] = {
        {{50, 50}, {150, 150}},
        {{200, 100}, {400, 300}},
        {{300, 50}, {500, 250}}
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
                    XFillArc(display, window, gc, 
                        points[i].x - 3, points[i].y - 3, 
                        6, 6, 0, 360 * 64);
                }
                
                // Draw lines
                for (int i = 0; i < 3; i++) {
                    XDrawLine(display, window, gc,
                        lines[i].start.x, lines[i].start.y,
                        lines[i].end.x, lines[i].end.y);
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
