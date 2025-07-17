#include <raylib.h>
#include <stdio.h>

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
} ViewCamera;

Point world_to_screen(float world_x, float world_y, ViewCamera* cam, int screen_width, int screen_height) {
    Point screen_point;
    screen_point.x = (int)((world_x - cam->center_x) * cam->zoom + screen_width / 2);
    screen_point.y = (int)((world_y - cam->center_y) * cam->zoom + screen_height / 2);
    return screen_point;
}

void draw_scene(ViewCamera* camera) {
    ClearBackground(BLACK);

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
        DrawCircle(screen_point.x, screen_point.y, 3, WHITE);
    }

    for (int i = 0; i < 4; i++) {
        Point start = world_to_screen(lines[i].start.x, lines[i].start.y, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        Point end = world_to_screen(lines[i].end.x, lines[i].end.y, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        DrawLine(start.x, start.y, end.x, end.y, WHITE);
    }

    DrawLine(0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT / 2, WHITE);
    DrawLine(SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2, SCREEN_HEIGHT, WHITE);

    char buf[128];
    snprintf(buf, sizeof(buf), "cam.x=%.2f cam.y=%.2f zoom=%.2f",
             camera->center_x, camera->center_y, camera->zoom);
    DrawText(buf, 10, 20, 20, WHITE);
}

int main() {
    ViewCamera camera;
    camera.center_x = 1.0f;
    camera.center_y = 1.0f;
    camera.zoom = 100.0f;

    InitWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Manual Render");
    SetTargetFPS(60);

    while (!WindowShouldClose()) {
        // Handle input
        if (IsKeyDown(KEY_EQUAL) || IsKeyDown(KEY_KP_ADD)) {
            camera.zoom += 10.0f;
        }
        if (IsKeyDown(KEY_MINUS) || IsKeyDown(KEY_KP_SUBTRACT)) {
            if (camera.zoom > 10.0f) {
                camera.zoom -= 10.0f;
            }
        }
        if (IsKeyDown(KEY_UP)) {
            camera.center_y -= 1.0f;
        }
        if (IsKeyDown(KEY_DOWN)) {
            camera.center_y += 1.0f;
        }
        if (IsKeyDown(KEY_LEFT)) {
            camera.center_x -= 1.0f;
        }
        if (IsKeyDown(KEY_RIGHT)) {
            camera.center_x += 1.0f;
        }
        if (IsKeyPressed(KEY_Q)) {
            break;
        }

        if (IsMouseButtonPressed(MOUSE_LEFT_BUTTON)) {
            Vector2 mouse_pos = GetMousePosition();
            printf("Mouse clicked at (%.0f, %.0f)\n", mouse_pos.x, mouse_pos.y);
        }

        // Draw
        BeginDrawing();
        draw_scene(&camera);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}

