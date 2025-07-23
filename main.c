#include <raylib.h>
#include <stdio.h>

#define SCREEN_WIDTH 800
#define SCREEN_HEIGHT 600

typedef struct {
    float x, y, z;
} Point;

typedef struct {
    Point start, end;
} Line;

typedef struct {
    float center_x, center_y, center_z;
} WorldCamera;




// Convert world coordinates to view coordinates by making camera the origin.
// This isolates camera position from projection math - objects are now positioned
// relative to where the camera is looking from, not their absolute world position.
Point world_to_view(Point world_point, WorldCamera* cam) {
    Point view_point;
    view_point.x = world_point.x - cam->center_x;
    view_point.y = world_point.y - cam->center_y;
    view_point.z = world_point.z - cam->center_z;
    return view_point;
}

// Apply perspective projection: flatten 3D space onto 2D screen plane.
// Only X,Y get perspective division because screens only have 2D pixels.
// Z is preserved for depth sorting/clipping but doesn't affect screen position.
// fov_scale controls field of view: higher = narrower view (telephoto), lower = wider view (wide-angle).
Point apply_perspective(Point view_point, float fov_scale) {
    Point proj_point;

    // Clip objects behind camera or too close (near plane)
    if (view_point.z <= 0.1f) {
        return (Point){0, 0, -1}; // signal that object should not be rendered
    }

    proj_point.x = view_point.x / view_point.z * fov_scale;
    proj_point.y = view_point.y / view_point.z * fov_scale;
    proj_point.z = view_point.z; // keep original depth for 3D operations
    return proj_point;
}

// Map projection coordinates to final screen pixel positions.
// Centers the image and scales to screen size - purely 2D transformation.
Point projection_to_screen(Point proj_point, int screen_width, int screen_height) {
    Point screen_point;
    screen_point.x = proj_point.x + screen_width / 2;
    screen_point.y = proj_point.y + screen_height / 2;
    screen_point.z = proj_point.z; // pass through depth
    return screen_point;
}

// Complete 3D pipeline: World → View → Projection → Screen
Point world_to_screen_pipeline(Point world_point, WorldCamera* cam, int screen_width, int screen_height) {
    Point view_point = world_to_view(world_point, cam);
    Point proj_point = apply_perspective(view_point, 100.0f); // fov_scale
    Point screen_point = projection_to_screen(proj_point, screen_width, screen_height);
    return screen_point;
}



void draw_scene(WorldCamera* camera) {
    ClearBackground(BLACK);

    Point points[] = {
        {0, 0, 0}, {2, 0, 0}, {2, 2, 0}, {0, 2, 0}
    };

    Line lines[] = {
        {{0, 0, 0}, {2, 0, 0}},
        {{2, 0, 0}, {2, 2, 0}},
        {{2, 2, 0}, {0, 2, 0}},
        {{0, 2, 0}, {0, 0, 0}}
    };

    for (int i = 0; i < 4; i++) {
        Point screen_point = world_to_screen_pipeline(points[i], camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        DrawCircle(screen_point.x, screen_point.y, 3, WHITE);
    }

    for (int i = 0; i < 4; i++) {
        Point start = world_to_screen_pipeline(lines[i].start, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        Point end = world_to_screen_pipeline(lines[i].end, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        DrawLine(start.x, start.y, end.x, end.y, WHITE);
    }

    DrawLine(0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT / 2, WHITE);
    DrawLine(SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2, SCREEN_HEIGHT, WHITE);

    char buf[128];
    snprintf(buf, sizeof(buf), "cam.x=%.2f cam.y=%.2f cam.z=%.2f",
             camera->center_x, camera->center_y, camera->center_z);
    DrawText(buf, 10, 20, 20, WHITE);
}

int main() {
    WorldCamera camera;
    camera.center_x = 0.0f;
    camera.center_y = 0.0f;
    camera.center_z = -1.0f; 

    InitWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Manual Render");
    SetTargetFPS(60);

    while (!WindowShouldClose()) {
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
        if (IsKeyDown(KEY_Y)) {
            camera.center_z -= 1.0f;
        }
        if (IsKeyDown(KEY_U)) {
            camera.center_z += 1.0f;
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

