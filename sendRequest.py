from locust import HttpUser, task
import requests
import base64
import json
import os
import uuid
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth("flask", "FIT5225")  # code from tutorial


class InternetUser(HttpUser):

    @task
    def post_to_server(self):

        #Path of the input folder
        image_folder_path = ''

        for filename in os.listdir(image_folder_path):

            if filename.endswith(".jpg"):

                # join the folder path and file name as image path
                image_path = os.path.join(image_folder_path, filename)

                # Generate a unique ID for the image
                image_id = str(uuid.uuid4())

                # Encode the image to base64
                encoded_image = encode_image_to_base64(image_path)

                # send_data = json format { id, base64-encoded image }
                send_data = {
                    "id": image_id,
                    "image": encoded_image
                }

                print("Sending request!")
                response = self.client.post("/input", json={"id": image_id, "image": encoded_image}, auth=auth)

                # if successful:
                if response.status_code == 200:
                    print(response.json())

                else:
                    print("No response, Status Code : ", response.status_code)


# From Chatgpt
def encode_image_to_base64(image_path):
    '''
    input:image_path
    output: encoded image 64

    Encode a image by a given path and return the encoded image
    '''
    with open(image_path, "rb") as image_file:  # direct to the image path
        return base64.b64encode(image_file.read()).decode('utf-8')  # encode the image