import datetime
import json
import os
import time
import urllib.parse
from urllib3.filepost import encode_multipart_formdata, choose_boundary
from urllib3.fields import RequestField

import requests

from ..handler import BaseHandler


class GDriveHandler(BaseHandler):
    def __init__(
        self, client_id, redirect_uri, client_secret, scope, access_token=None, refresh_token=None, expiration_time=None
    ):
        super().__init__(client_id, redirect_uri, access_token, refresh_token, expiration_time)
        self.__client_secret = client_secret
        self.scope = scope

    def authenticate(self, scope=None):
        challenges = self._generate_code()
        code_verifier = challenges[0]
        code_challenge = challenges[1]
        if scope is None:
            scope = self.scope

        base_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        authorization_url = f"{base_auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope}&access_type=offline&code_challenge_method=S256&code_challenge={code_challenge}"
        print("Step 1: Please visit this URL to authenticate:", authorization_url)
        code = input("Step 2: please input a code: ")
        code = urllib.parse.unquote(code)
        token_url = "https://oauth2.googleapis.com/token"
        body = {
            "client_id": self.client_id,
            "client_secret": self.__client_secret,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        base_time = datetime.datetime.now()
        # Todo: add error handling
        response = requests.post(token_url, body)

        if response.status_code == 200:
            response_body = json.loads(response.text)
            self.access_token = response_body["access_token"]
            self.refresh_token = response_body["refresh_token"]
            expires_in = response_body["expires_in"]

            safety_margin_sec = 120
            delta = datetime.timedelta(seconds=expires_in - safety_margin_sec)
            self.expiration_time = base_time + delta
            return True
        else:
            print(f"code exchange failed: {response.text}")
            return False

    def token_refresh(self):
        if self.refresh_token is None:
            print("No refresh token available. Please authenticate at first.")
            return False
        else:
            base_time = datetime.datetime.now()
            url = "https://oauth2.googleapis.com/token"
            body = {"grant_type": "refresh_token", "client_id": self.client_id, "refresh_token": self.refresh_token}
            response = requests.post(url, body)

            if response.status_code == 200:
                response_body = json.loads(response.text)
                self.access_token = response_body["access_token"]
                expires_in = response_body["expires_in"]

                safety_margin_sec = 120
                delta = datetime.timedelta(seconds=expires_in - safety_margin_sec)
                self.expiration_time = base_time + delta
                return True
            else:
                print(f"code exchange failed: {response.text}")
                return False

    def encode_multipart_related(self, fields, boundary=None):
        if boundary is None:
            boundary = choose_boundary()

        body, _ = encode_multipart_formdata(fields, boundary)
        content_type = str("multipart/related; boundary=%s" % boundary)

        return body, content_type

    def encode_media_related(self, metadata, media, media_content_type):
        rf1 = RequestField(
            name="placeholder",
            data=json.dumps(metadata),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        rf2 = RequestField(
            name="placeholder2",
            data=media,
            headers={"Content-Type": media_content_type},
        )
        return self.encode_multipart_related([rf1, rf2])

    def upload_file(self, local_path, destination_path, __retry_count=0):
        file_name = os.path.basename(local_path)
        binary_data = None

        if os.path.exists(local_path):
            with open(local_path, mode="ra") as fp:
                binary_data = fp.read()

            metadata = {
                "mimeType": "text/plain",
                "name": file_name,
            }
            body, content_type = self.encode_media_related(
                metadata,
                binary_data,
                "text/plain",
            )
            response = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                body,
                params={"uploadType": "multipart"},
                headers={"Content-Type": content_type, "Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                self.token_refresh()
                return self.upload_file(local_path, destination_path, __retry_count)
            else:
                print(f"Unkown error: {response.status_code}, {response.text}")
                if __retry_count < 3:
                    time.sleep(3)
                    return self.upload_file(local_path, destination_path, __retry_count + 1)
                else:
                    print("stop uploading files as it files several times.")
                    return False
        else:
            print(f"{local_path} not found.")
            return False

    def download_file(self, destination_file_path, local_path_to_save, __retry_count=0):
        pass
