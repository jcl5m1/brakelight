# Brake Light Detector
OpenCV python code for detecting brake light activation.  Detection code auto-calirbates min/max pixel values within each detection region to compute detection threshold.  Detection regions are defined in a json file.

![Example image](https://github.com/jcl5m1/brakelight/blob/main/images/example.jpg?raw=true)

Output `{'left': False, 'center': False, 'right': True}`

Run with test images:
`python main.py --test`

Run with webcam:
`python main.py`

Press escape to quit
