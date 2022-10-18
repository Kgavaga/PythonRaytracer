import math
from turtle import position
import numpy as np
import pygame
import os
from pygame.locals import *
from time import sleep, time

WIDTH = 1280
HEIGHT = 720

WIDTH = 200
HEIGHT = 100
AA = True
windowAlive = True

class Window:
    def __init__(self, windowTitle):
        self.windowTitle = windowTitle
        self.screen, self.font = self.__initWindow__(windowTitle)

    def __initWindow__(self, windowTitle):
        os.environ['SDL_VIDEO_WINDOW_POS'] = '{},{}'.format(100, 100)
        
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
        pygame.font.init()
        myfont = pygame.font.SysFont('Arial', 30)
        pygame.display.set_caption(windowTitle)
        return (screen, myfont)

    def getWidth(self):
        return self.screen.get_width()

    def getHeight(self):
        return self.screen.get_height()

    def isWindowClosed(self):
        for events in pygame.event.get():
            if events.type == QUIT:
                return True
        return False

    def drawPixel(self, screen, x, y, color):
        screen.set_at((x, y), color)

    def drawPixels(self, screen, pixels):
        screenWidth = self.getWidth()
        screenHeight = self.getHeight()
        for y in range(screenHeight):
            for x in range(screenWidth):
                self.drawPixel(screen, x, screenHeight-y, pixels[x+y*screenWidth])

    def refreshScreen():
        pygame.display.update()

def normalize(vector):
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm

class Collideable:
    def collidesWith(self, rayOrigin, rayDirection):
        raise NotImplemented()

class Camera:
    def __init__(self, position, direction, fov, screenRatio): # screenRatio (e.g. 9/16)
        self.position = position
        self.direction = direction
        self.fov = fov
        tangent = 1/screenRatio
        self.distanceFromProjectionPlane = abs(tangent/math.tan(math.radians(fov/2)))

class Light:
    def __init__(self, position, color):
        self.position = position
        self.color = color

class Sphere (Collideable):
    def __init__(self, position, radius, color):
        self.position = position
        self.radius = radius
        self.color = color
        self.ambientStrength = 0.1
        self.specularStrength = 0.8
        self.specularExponent = 128.0
        
    def collidesWith(self, rayOrigin, rayDirection):
        b = 2 * np.dot(rayDirection, rayOrigin - self.position)
        c = np.linalg.norm(rayOrigin - self.position) ** 2 - self.radius ** 2
        delta = b ** 2 - 4 * c
        if delta > 0:
            t1 = (-b + np.sqrt(delta)) / 2
            t2 = (-b - np.sqrt(delta)) / 2
            if t1 > 0 and t2 > 0:
                return min(t1, t2)
        return None
 

class Scene:
    def __init__(self, camera: Camera, objects: Collideable, light: Light, backgroundColor):
        self.camera = camera
        self.objects = objects
        self.light = light
        self.backgroundColor = backgroundColor

    def getRay(self, x, y, screenWidth, screenHeight, camera): # Not yet able to deal with rotated camera
        pixelPosition = np.array([
            ((x/screenWidth)-0.5)*screenWidth/screenHeight,
            (y/screenHeight)-0.5,
            -camera.distanceFromProjectionPlane
        ])
        return normalize(pixelPosition)

    def collideWithClosest(self, shapes:Collideable, rayOrigin, rayDirection):
        timesOfCollisonList = []
        for shape in shapes: # look at the rest of the shapes
            timesOfCollisonList.append(shape.collidesWith(rayOrigin, rayDirection))

        closestShape = None
        timeOfClosestCollison = np.inf
        for shapeIndex, time in enumerate(timesOfCollisonList):
            if time and time < timeOfClosestCollison:
                closestShape = shapes[shapeIndex]
                timeOfClosestCollison = time
        
        if timeOfClosestCollison != np.inf:
            collisionPoint = rayOrigin + rayDirection*timeOfClosestCollison
            return closestShape, collisionPoint
        return None, None

    def getColor(self, rayOrigin, rayDirection, iteration):
        color = self.backgroundColor
        hitObject, collisonPoint = self.collideWithClosest(self.objects, rayOrigin, rayDirection)
        if hitObject != None:  
            objectNormalVector = normalize(collisonPoint-hitObject.position)
            lightDirection = normalize(self.light.position - collisonPoint)
            diffuseStrength = max(0.0,np.dot(lightDirection,objectNormalVector))
            
            cameraDirection = normalize(self.camera.position - collisonPoint)
            specular = max(0.0,np.dot(objectNormalVector, normalize(lightDirection+cameraDirection)))**hitObject.specularExponent

            color = hitObject.color*self.light.color*(
                        hitObject.ambientStrength + diffuseStrength + hitObject.specularStrength*specular
                    )
            
            if iteration < 4:
                reflectedDirection = rayDirection-2.0*np.dot(rayDirection,objectNormalVector)*objectNormalVector
                color += 0.2* self.getColor(collisonPoint, reflectedDirection, iteration+1)
            
        return color

    def render(self, screenWidth, screenHeight, onPixelCalculated):
        for y in range(screenHeight):
            for x in range(screenWidth):
                color = np.array([0,0,0])
                global AA
                if AA == True:
                    for i in range(-1, 2, 1):
                        for j in range(-1,2, 1):
                            rayDirection = self.getRay(x+i*0.3, y+j*0.3, screenWidth, screenHeight, self.camera)
                            color = color + self.getColor(self.camera.position, rayDirection, 1)
                    color /= 9.0
                else:
                    rayDirection = self.getRay(x, y, screenWidth, screenHeight, self.camera)
                    color = self.getColor(self.camera.position, rayDirection, 1)
                onPixelCalculated(tuple(np.clip(color, 0, 255)))
            print("Progress: {}%".format(y*100/screenHeight))


def main():
    # Init Screen
    window = Window("Raytracer")
    screenWidth = screen.get_width()
    screenHeight = screen.get_height()
    screenRatio = screenHeight/screenWidth
    print("Width: {}; Height: {}".format(screenWidth, screenHeight))

    # Setup Camera
    camera = Camera(np.array([0.0,1.0,5.0]), np.array([0.0,0.0,-1.0]), 100.0, screenRatio)

    # Setup Spheres
    spheres: Collideable = []
    spheres.append(Sphere(np.array([-1.0, 1, -1]), 1.0, np.array([0.1, 0.3, 0.7])))
    spheres.append(Sphere(np.array([1.0, 0.3, 0]), 0.3, np.array([0.5, 0.1, 0.4])))
    spheres.append(Sphere(np.array([0.0, -900.0, 0.0]), 900.0, np.array([0.9, 0.9, 0.9]))) # Sealing
    spheres.append(Sphere(np.array([0.0, +903.0, 0.0]), 900.0, np.array([0.9, 0.9, 0.9]))) # Floor
    spheres.append(Sphere(np.array([-903.0, 0.0, 0.0]), 900.0, np.array([1.0, 0.0, 0.0]))) # Left Wall
    spheres.append(Sphere(np.array([+903.0, 0.0, 0.0]), 900.0, np.array([0.0, 0.0, 1.0]))) # Right Wall
    spheres.append(Sphere(np.array([0.0, 0.0, -903.0]), 900.0, np.array([0.9, 0.9, 0.9]))) # Back Wall

    # Setup Light
    light = Light(np.array([5.0, 5.0, 5.0]), np.array([255, 255, 255])) 

    # Setup Background
    backgroundColor = np.array([50, 50, 100])

    # Create Scene
    scene = Scene(camera, spheres, light, backgroundColor)

    while windowAlive:

        pixels = []
        onPixelColor = lambda color: pixels.append(color)
        scene.render(screenWidth, screenHeight, onPixelColor)
        print(len(pixels))
        drawPixels(screen, pixels)
        #camera.fov += 1.0
        #camera.position[2] += 1.0
        isWindowClosed()
        refreshScreen()

    return 0


if __name__ == "__main__":
    main()
