# import the necessary packages
import numpy as np
import sys
import time
import cv2
import os
from threading import Thread, Lock
from flask import Flask, request, jsonify
import base64


def get_labels(labels_path):
    # load the COCO class labels our YOLO model was trained on
    lpath = os.path.sep.join([yolo_path, labels_path])

    print(yolo_path)
    LABELS = open(lpath).read().strip().split("\n")
    return LABELS


def get_weights(weights_path):
    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.sep.join([yolo_path, weights_path])
    return weightsPath


def get_config(config_path):
    configPath = os.path.sep.join([yolo_path, config_path])
    return configPath


def load_model(configpath, weightspath):
    # load our YOLO object detector trained on COCO dataset (80 classes)
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net


def do_prediction(image, net, LABELS):
    lock.acquire()  # lock do_prediction()

    (H, W) = image.shape[:2]
    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    # print(layerOutputs)
    end = time.time()

    # show timing information on YOLO
    # print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])

                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)

    # TODO Prepare the output as required to the assignment specification

    # capture the result
    result = []

    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # append to list
            result.append({
                "label": LABELS[classIDs[i]],
                "accuracy": confidences[i],
                "rectangle": {
                    "left": boxes[i][0],
                    "top": boxes[i][1],
                    "width": boxes[i][2],
                    "height": boxes[i][3]
                }
            })

    lock.release()  # relase the lock after prediction is done
    return result


# construct the argument parse and parse the arguments
confthres = 0.3
nmsthres = 0.1

# Local path for yolo_tiny configs model
# yolo_path = '~/yolo_tiny_configs'

# Container path
yolo_path = '/app/yolo_tiny_configs'

## Yolov3-tiny versrion
labelsPath = "coco.names"
cfgpath = "yolov3-tiny.cfg"
wpath = "yolov3-tiny.weights"
Lables = get_labels(labelsPath)
CFG = get_config(cfgpath)
Weights = get_weights(wpath)

# load model
nets = load_model(CFG, Weights)
# import lock object
lock = Lock()

app = Flask(__name__)

@app.route('/input', methods=['POST'])
def object_detection_service():
    '''
    Detect the image in the client post request and return the result

    input:none
    output:none
    '''
    # Get data from request
    post_request_data = request.json
    client_id = post_request_data['id']  # client id
    encoded_image = post_request_data['image']  # encoded image

    # Decoding process from Chatgpt
    decoded_image = base64.b64decode(encoded_image)  # decode the image send from client
    nparr = np.frombuffer(decoded_image, np.uint8)  # Convert the decoded image to a format OpenCV can read
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_np = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)  # Convert color space

    # do prediction
    prediction_res = do_prediction(img_np, nets, Lables)  # do prediction
    output = jsonify({"id": client_id, "objects": prediction_res})  # adjust return format
    return output


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)