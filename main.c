#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>

#define SCREEN_WIDTH 800
#define SCREEN_HEIGHT 600

typedef struct {
    int x, y;
} Point;

typedef struct {
    Point start, end;
} Line;

typedef struct {
    float center_x, center_y;
    float zoom;
} Camera;

Point world_to_screen(float world_x, float world_y, Camera* cam, int screen_width, int screen_height) {
    Point screen_point;
    screen_point.x = (int)((world_x - cam->center_x) * cam->zoom + screen_width / 2);
    screen_point.y = (int)((world_y - cam->center_y) * cam->zoom + screen_height / 2);
    return screen_point;
}

void draw_scene(Display* display, Window window, GC gc, Camera* camera) {
    XClearWindow(display, window);

    Point points[] = {
        {0, 0}, {2, 0}, {2, 2}, {0, 2}
    };

    Line lines[] = {
        {{0, 0}, {2, 0}},
        {{2, 0}, {2, 2}},
        {{2, 2}, {0, 2}},
        {{0, 2}, {0, 0}}
    };

    for (int i = 0; i < 4; i++) {
        Point screen_point = world_to_screen(points[i].x, points[i].y, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        XFillArc(display, window, gc, screen_point.x - 3, screen_point.y - 3, 6, 6, 0, 360 * 64);
    }

    for (int i = 0; i < 4; i++) {
        Point start = world_to_screen(lines[i].start.x, lines[i].start.y, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        Point end = world_to_screen(lines[i].end.x, lines[i].end.y, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        XDrawLine(display, window, gc, start.x, start.y, end.x, end.y);
    }

    XDrawLine(display, window, gc, 0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT / 2);
    XDrawLine(display, window, gc, SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2, SCREEN_HEIGHT);

    char buf[128];
    snprintf(buf, sizeof(buf), "cam.x=%.2f cam.y=%.2f zoom=%.2f",
             camera->center_x, camera->center_y, camera->zoom);
    XDrawString(display, window, gc, 10, 20, buf, strlen(buf));
}

int main() {
    Display *display;
    Window window;
    XEvent event;
    int screen;
    GC gc;
    Camera camera;

    display = XOpenDisplay(NULL);
    if (display == NULL) {
        printf("Cannot open display\n");
        return 1;
    }

    screen = DefaultScreen(display);
    window = XCreateSimpleWindow(display, RootWindow(display, screen),
                                  10, 10, SCREEN_WIDTH, SCREEN_HEIGHT, 1,
                                  BlackPixel(display, screen),
                                  BlackPixel(display, screen));

    XSelectInput(display, window, ExposureMask | KeyPressMask | ButtonPressMask);
    XMapWindow(display, window);
    gc = XCreateGC(display, window, 0, NULL);
    Font font = XLoadFont(display, "10x20");
    XSetFont(display, gc, font);
    XSetForeground(display, gc, WhitePixel(display, screen));

    camera.center_x = 1.0f;
    camera.center_y = 1.0f;
    camera.zoom = 100.0f;

    while (1) {
        XNextEvent(display, &event);

        switch (event.type) {
            case Expose:
                draw_scene(display, window, gc, &camera);
                break;

            case KeyPress: {
                KeySym key = XLookupKeysym(&event.xkey, 0);
                int moved = 0;

                switch (key) {
                    case XK_plus:
                    case XK_equal:  // usually '=' is used for '+'
                        camera.zoom += 10.0f;
                        moved = 1;
                        break;
                    case XK_minus:
                        if (camera.zoom > 10.0f) {
                            camera.zoom -= 10.0f;
                            moved = 1;
                        }
                        break;
                    case XK_Up:
                        camera.center_y -= 1.0f;
                        moved = 1;
                        break;
                    case XK_Down:
                        camera.center_y += 1.0f;
                        moved = 1;
                        break;
                    case XK_Left:
                        camera.center_x -= 1.0f;
                        moved = 1;
                        break;
                    case XK_Right:
                        camera.center_x += 1.0f;
                        moved = 1;
                        break;
                    case XK_q:
                        goto cleanup;
                }

                if (moved) {
                    draw_scene(display, window, gc, &camera);
                }
                break;
            }

            case ButtonPress:
                printf("Mouse clicked at (%d, %d)\n", event.xbutton.x, event.xbutton.y);
                break;
        }
    }

cleanup:
    XFreeGC(display, gc);
    XDestroyWindow(display, window);
    XCloseDisplay(display);
    return 0;
}

