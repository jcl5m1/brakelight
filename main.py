import cv2
import numpy as np
import time
import argparse
import json
import math
from scipy.spatial.transform  import Rotation as R

IMAGES = [
    'images/modelY_off.jpg',
    'images/modelY_left.jpg',
    'images/modelY_right.jpg',
    'images/modelY_brake.jpg'
]

LOCATION_FILE = "locations.json"
WIDTH = 640
HEIGHT = 480

# minimum pixel max-min difference in the red channel to avoid triggering on noise
# tap the brakes to calibrate min/max values
MINIMUM_DIFF = 5 

light_stats = {}

cam = None

# light locations are fixed in pixel space.
# if the trailer is at an angle, need to compensate.  
# Can be done with a homography & estimated angle and camera FOV
with open(LOCATION_FILE) as fp:
    light_locations = json.load(fp)

def warpImage(img, car_yaw, car_pitch, cam_vertfov):
    # simplistic car centering adjustment
    # assumes pinhole camera

    f = 480*45/cam_vertfov
    dist = 2*45/cam_vertfov
    aspect = WIDTH/HEIGHT
    pts = np.array([[-aspect,-1,dist,1],[aspect,-1,dist,1],[aspect,1,dist,1],[-aspect,1,dist,1]], dtype=np.float32).T
    transform_matrix = np.identity(4)
    transform_matrix[:3,:3] = R.from_euler('xy',[math.radians(car_pitch),math.radians(car_yaw)]).as_matrix()
    projection_matrix = np.array([[1,0,0,0],[0,1,0,0],[0,0,1/f,0],[0,0,0,1]], dtype=np.float32)

    pts = np.matmul(transform_matrix, pts)
    pts = np.matmul(projection_matrix, pts).T
    for p in pts:
        p /= p[2]
        p[0] += WIDTH/2
        p[1] += HEIGHT/2

    src_pts = np.array([[0,0],[WIDTH,0],[WIDTH,HEIGHT],[0,HEIGHT]], dtype=np.float32)
    dst_pts = np.array([[pts[0][0],pts[0][1]],
                        [pts[1][0],pts[1][1]],
                        [pts[2][0],pts[2][1]],
                        [pts[3][0],pts[3][1]]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    return cv2.warpPerspective(img, M, (WIDTH, HEIGHT));


def drawLight(img, light, detected):
    thickness = 1
    if detected:
        thickness = 5
    cv2.rectangle(img, 
        (light["bounds"]["x1"], light["bounds"]["y1"]),
        (light["bounds"]["x2"], light["bounds"]["y2"]),
        (0,255,255),thickness)

def detectLight(img, light):
    # simple adaptive min/max calibration and average thresholding
    id = light["id"]
    if id not in light_stats:
        light_stats[id] = {
            "min":255,
            "max":0,
        }

    # compute mean pixel value in the red channel
    mean = np.mean(img[light["bounds"]["y1"]:light["bounds"]["y2"],
        light["bounds"]["x1"]:light["bounds"]["x2"],2])

    if light_stats[id]["min"] > mean:
        light_stats[id]["min"] = mean
    if light_stats[id]["max"] < mean:
        light_stats[id]["max"] = mean

    if light_stats[id]["max"] > light_stats[id]["min"] + MINIMUM_DIFF:
        return mean > (light_stats[id]["max"] + light_stats[id]["min"])/2
    else:
        return False

def getImage(use_test_images):
    global cam
    if use_test_images:
        return  cv2.imread(IMAGES[ (int)(time.time())%len(IMAGES)])
    else:
        if cam is None:
            cam = cv2.VideoCapture(0)
            cam.set(3, 640)
            cam.set(4, 480)
        _, img = cam.read()
        return img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true', help='use test images')
    args = parser.parse_args()

    while True:
        img = getImage(args.test)
        img = warpImage(img, 0,0,45)
        state = {}
        for id in light_locations:
            detected = detectLight(img, light_locations[id])
            state[id] = detected
            drawLight(img, light_locations[id],detected)
        print(state)

        cv2.imshow("Images", img)
        c = cv2.waitKey(1) & 0xFF
        if c == 27:
            break

if __name__ == "__main__":
    main()