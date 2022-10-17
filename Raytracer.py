import numpy as np
import sys
import pygame
import os
from pygame.locals import *
from time import sleep, time

WIDTH = 200
HEIGHT = 200
windowAlive = True


def initPygame():
    os.environ['SDL_VIDEO_WINDOW_POS'] = '{},{}'.format(100, 200)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.font.init()
    myfont = pygame.font.SysFont('Arial', 30)
    pygame.display.set_caption("NumberReader")
    return (screen, myfont)


def checkAndActOnEvents():
    for events in pygame.event.get():
        if events.type == QUIT:
            global windowAlive
            windowAlive = False
            sys.exit()


def drawPixel(screen, x, y, color):
    pygame.draw.rect(screen, color, (x, y, 1, 1), 0)


def refreshScreen():
    pygame.display.update()


def normalize(vector):
    return vector / np.linalg.norm(vector)
    
def sphereIntersect(spherePosition, sphereRadius, rayOrigin, rayDirection):
    b = 2 * np.dot(rayDirection, rayOrigin - spherePosition)
    c = np.linalg.norm(rayOrigin - spherePosition) ** 2 - sphereRadius ** 2
    delta = b ** 2 - 4 * c
    if delta > 0:
        t1 = (-b + np.sqrt(delta)) / 2
        t2 = (-b - np.sqrt(delta)) / 2
        if t1 > 0 and t2 > 0:
            return rayOrigin+rayDirection*min(t1, t2)
    return None


def getRay(x, y, screenWidth, screenHeight, cameraPosition):

    pixelPosition = np.array([
        ((x/screenWidth)-0.5)*screenWidth/screenHeight,
        (y/screenHeight)-0.5,
        cameraPosition[2]-1
    ])
    return normalize(pixelPosition-cameraPosition)

def main():
    # Init Screen
    screen, font = initPygame()
    screenWidth = screen.get_width()
    screenHeight = screen.get_height()
    print("Width: {}; Height: {}".format(screenWidth, screenHeight))

    # Setup Background
    backgroundColor = (25, 25, 25)

    # Setup Camera
    cameraPosition = np.array([0.0, 0.0, -4.0])

    # Setup Sphere
    spherePosition = np.array([0.0, 0.0, -10.0])
    sphereRadius = 3.0
    sphereColor = np.array([0.1, 0.3, 0.7])    

    # Setup Light
    lightPosition = np.array([0.0, 5.0, 0.0])
    lightColor = np.array([255, 255, 255])


    # Keep window alive
    while windowAlive:
        for y in range(screenHeight):
            for x in range(screenWidth):
                rayDirection = getRay(x, y, screenWidth, screenHeight, cameraPosition)

                intersectionPoint = sphereIntersect(spherePosition, sphereRadius, cameraPosition, rayDirection)
                if type(intersectionPoint) != type(None):
                    sphereColor = np.array([0.1, 0.3, 0.7])    
                    sphereNormalVector = normalize(intersectionPoint-spherePosition)
                    lightDirection = normalize(lightPosition - intersectionPoint)
                    dotProduct = max(0.0,np.dot(lightDirection,sphereNormalVector))

                    color = tuple(lightColor*sphereColor*dotProduct)
                else:
                    color = backgroundColor
                drawPixel(screen, screenWidth-x, screenHeight-y, color) 
                checkAndActOnEvents()
        
        refreshScreen()
        cameraPosition[2] -= 1.0

    return 0


if __name__ == "__main__":
    main()
