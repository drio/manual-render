#include "raylib.h"
#include <math.h>

int main(void)
{
    // Window initialization
    const int screenWidth = 1024;
    const int screenHeight = 800;
    InitWindow(screenWidth, screenHeight, "Raylib 3D - Planes and Orbiting Camera");
    
    // Camera setup
    // Raylib uses the poosition, target and up vectors to build the view matrix
    Camera3D camera = { 0 };
    // It will get updated in the first loop
    camera.position = (Vector3){ 20.0f, 10.0f, 20.0f };  // Start position
    camera.target = (Vector3){ 0.0f, 0.0f, 0.0f };      // Looking at origin
    camera.up = (Vector3){ 0.0f, 1.0f, 0.0f };          // Y is up
    camera.fovy = 45.0f;                                 // Field of view
    camera.projection = CAMERA_PERSPECTIVE;              // Perspective projection
    
    // Orbit parameters
    float orbitRadius = 30.0f;  // Distance from origin
    float orbitHeight = 20.0f;   // Height above ground
    float orbitAngle = 0.0f;    // Current angle in radians
    float orbitSpeed = 0.5f;     // Radians per second
    
    // Set target FPS (optional, raylib runs at 60 by default)
    SetTargetFPS(60);
    
    // Main game loop
    while (!WindowShouldClose())    // Detect window close or ESC key
    {
        // Update camera position (orbiting)
        // Calculate new camera position in XZ plane
        orbitAngle += orbitSpeed * GetFrameTime();  // GetFrameTime() returns delta time
        camera.position.x = cosf(orbitAngle) * orbitRadius;
        camera.position.z = sinf(orbitAngle) * orbitRadius;
        camera.position.y = orbitHeight;  // Keep constant height
        
        // Camera always looks at origin
        camera.target = (Vector3){ 0.0f, 0.0f, 0.0f };
        
        // Start drawing
        BeginDrawing();
            ClearBackground(BLACK);
            
            // Begin 3D mode with our camera
            BeginMode3D(camera);
                
                // Draw grey floor plane (XZ plane)
                // DrawPlane takes: center position, size (Vector2), color
                DrawPlane(
                    (Vector3){ 0.0f, 0.0f, 0.0f },  // Center at origin
                    (Vector2){ 10.0f, 10.0f },      // 10x10 units size
                    GRAY                             // Grey color
                );
                
                // Draw red vertical plane (YZ plane)
                // We'll use DrawCube and make it very thin in X direction
                // DrawCube takes: center position, width, height, length, color
                DrawCube(
                    (Vector3){ 0.0f, 5.0f, 0.0f },  // Center, raised up
                    0.1f,                            // Very thin in X
                    10.0f,                           // Height in Y
                    10.0f,                           // Length in Z
                    RED                              // Red color
                );
                
                // Draw coordinate axes for reference
                DrawLine3D((Vector3){0,0,0}, (Vector3){15,0,0}, RED);     // X axis
                DrawLine3D((Vector3){0,0,0}, (Vector3){0,15,0}, GREEN);   // Y axis
                DrawLine3D((Vector3){0,0,0}, (Vector3){0,0,15}, BLUE);    // Z axis
                
                // Draw grid for better spatial reference
                DrawGrid(20, 1.0f);
                
            EndMode3D();
            
            // Draw FPS in top-left corner (2D text)
            DrawFPS(10, 10);
            
            // Additional debug info
            DrawText("X axis", 10, 35, 20, RED);
            DrawText("Y axis", 10, 60, 16, GREEN);
            DrawText("Z axis", 10, 80, 16, BLUE);
            
        EndDrawing();
    }
    
    // Clean up
    CloseWindow();
    
    return 0;
}
