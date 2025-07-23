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
    float zoom;
} WorldCamera;

typedef struct {
    float x, y;          // World position
    float width, height; // World dimensions
    Texture2D texture;   // The loaded texture
} WorldImage;



Point world_to_screen(Point world_point, WorldCamera* cam, int screen_width, int screen_height) {
    Point screen_point;
    screen_point.x = (world_point.x - cam->center_x) * cam->zoom + screen_width / 2;
    screen_point.y = (world_point.y - cam->center_y) * cam->zoom + screen_height / 2;
    screen_point.z = (world_point.z - cam->center_z) * cam->zoom;
    return screen_point;
}

void draw_image(WorldImage* img, WorldCamera* camera) {
    // where do the (x,y) coordinate of our image in our world map in the screen?
    Point world_pos = {img->x, img->y, 0.0f};
    Point screen_pos = world_to_screen(world_pos, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
    
    // Same, but how big the image should be in our screen?
    float screen_width = img->width * camera->zoom;
    float screen_height = img->height * camera->zoom;

    Rectangle source = (Rectangle){0, 0, img->texture.width, img->texture.height};
    Rectangle dest = (Rectangle){screen_pos.x, screen_pos.y, screen_width, screen_height};
    Vector2 origin = {0,0};
    float rotation = 0.0f;

    // Now we tell raylib to draw the image/texture with dimensions defined by the 
    // rectangle created above. 
    DrawTexturePro(img->texture, source, dest, origin, rotation, WHITE);
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
        Point screen_point = world_to_screen(points[i], camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        DrawCircle(screen_point.x, screen_point.y, 3, WHITE);
    }

    for (int i = 0; i < 4; i++) {
        Point start = world_to_screen(lines[i].start, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        Point end = world_to_screen(lines[i].end, camera, SCREEN_WIDTH, SCREEN_HEIGHT);
        DrawLine(start.x, start.y, end.x, end.y, WHITE);
    }

    DrawLine(0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT / 2, WHITE);
    DrawLine(SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2, SCREEN_HEIGHT, WHITE);

    char buf[128];
    snprintf(buf, sizeof(buf), "cam.x=%.2f cam.y=%.2f cam.z=%.2f zoom=%.2f",
             camera->center_x, camera->center_y, camera->center_z, camera->zoom);
    DrawText(buf, 10, 20, 20, WHITE);
}

int main() {
    WorldCamera camera;
    camera.center_x = 1.0f;
    camera.center_y = 1.0f;
    camera.center_z = 0.0f;
    camera.zoom = 100.0f;


    InitWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Manual Render");
    SetTargetFPS(60);

    Texture2D texture = LoadTexture("assets/rc.png");

    WorldImage rc_image;
    rc_image.x = 0.5f;      // World X position
    rc_image.y = 0.5f;      // World Y position
    rc_image.width = 1.0f;  // World width
    rc_image.height = 1.0f; // World height
    rc_image.texture = texture;

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
        draw_image(&rc_image, &camera);  // Draw the image
        EndDrawing();
    }

    UnloadTexture(texture);
    CloseWindow();
    return 0;
}

