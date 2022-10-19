import math
import sys
from threading import Thread
import numpy as np
import pygame
import os
from pygame.locals import *
from time import sleep, time

WIDTH = 1280
HEIGHT = 720

WIDTH = 500
HEIGHT = 500
AA = False
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

    def drawPixel(self, x, y, color):
        self.screen.set_at((x, y), color)

    def drawPixels(self, pixels):
        screenWidth = self.getWidth()
        screenHeight = self.getHeight()
        for y in range(screenHeight):
            for x in range(screenWidth):
                if x+y*screenWidth < len(pixels):
                    self.drawPixel(x, screenHeight-y, pixels[x+y*screenWidth])
                else:
                    return

    def refreshScreen(self):
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
        self.screenRatio = screenRatio
        self.distanceFromProjectionPlane = self.calculateDistanceFromProjectionPlane(screenRatio,fov)

    def calculateDistanceFromProjectionPlane(self, screenRatio, fov):
        tangent = 1/screenRatio
        return abs(tangent/math.tan(math.radians(fov/2)))

class Light:
    def __init__(self, position, color):
        self.position = position
        self.color = color

class Sphere (Collideable):
    def __init__(self, position, radius, color, ambientStrength = 0.1, specularStrength = 0.8, specularExponent = 128.0):
        self.position = position
        self.radius = radius
        self.color = color
        self.ambientStrength = ambientStrength
        self.specularStrength = specularStrength
        self.specularExponent = specularExponent
        
    def collidesWith(self, rayOrigin, rayDirection):
        b = 2 * np.dot(rayDirection, rayOrigin - self.position)
        c = np.linalg.norm(rayOrigin - self.position) ** 2 - self.radius ** 2
        delta = b ** 2 - 4 * c
        if delta > 0:
            # t1 = (-b + np.sqrt(delta)) / 2
            # t2 = (-b - np.sqrt(delta)) / 2
            # if t1 > 0 and t2 > 0:
            #     return min(t1, t2)
            t2 = (-b - np.sqrt(delta)) / 2
            if t2 > 0:
                return t2
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
        closestShape = None
        timeOfClosestCollison = np.inf
        for shapeIndex in range(len(shapes)):
            time = shapes[shapeIndex].collidesWith(rayOrigin, rayDirection)
            if time and time < timeOfClosestCollison:
                closestShape = shapes[shapeIndex]
                timeOfClosestCollison = time
        
        if timeOfClosestCollison != np.inf:
            collisionPoint = rayOrigin + rayDirection*timeOfClosestCollison
            return closestShape, collisionPoint
        return None, None

    def getColor(self, rayOrigin, rayDirection, depth):
        color = self.backgroundColor
        hitObject, collisonPoint = self.collideWithClosest(self.objects, rayOrigin, rayDirection)
        if hitObject != None:  
            objectNormalVector = normalize(collisonPoint-hitObject.position)
            fromObjectToLightVector = normalize(self.light.position - collisonPoint)
            diffuseStrength = max(0.0,np.dot(fromObjectToLightVector,objectNormalVector))
            
            fromObjectToCameraVector = normalize(self.camera.position - collisonPoint)
            specular = max(0.0,np.dot(objectNormalVector, normalize(fromObjectToLightVector+fromObjectToCameraVector)))**hitObject.specularExponent

            color = hitObject.color*self.light.color*(
                hitObject.ambientStrength + diffuseStrength + hitObject.specularStrength*specular
            )
            
            if depth < 4:
                reflectedDirection = rayDirection-2.0*np.dot(rayDirection,objectNormalVector)*objectNormalVector
                color += 0.2* self.getColor(collisonPoint, reflectedDirection, depth+1)
            
        return color

    def render(self, screenWidth, screenHeight, pixels):
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
                pixels.append(tuple(np.clip(color, 0, 255)))

            print("Progress: {}%".format(y*100/screenHeight))
        print("Progress: 100%")


def main():
    # Setup Window
    window = Window("Raytracer")
    windowWidth = window.getWidth()
    windowHeight = window.getHeight()
    windowRatio = float(windowHeight)/float(windowWidth)
    print("Width: {}; Height: {}".format(windowWidth, windowHeight))

    # Setup Camera
    camera = Camera(np.array([0.0,1.0,5.0]), np.array([0.0,0.0,-1.0]), 100.0, windowRatio)

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

    pixels = []
    renderThread = Thread(target=scene.render, args=[windowWidth, windowHeight, pixels], daemon=True)
    renderThread.start()

    while windowAlive:
        window.drawPixels(pixels)
        if(window.isWindowClosed()):
            sys.exit()
        window.refreshScreen()
        sleep(0.1)

    return 0

if __name__ == "__main__":
    main()
