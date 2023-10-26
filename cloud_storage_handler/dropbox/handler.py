import datetime
import json
import os
import time

import requests

from ..handler import BaseHandler


class DropboxHandler(BaseHandler):
    def __init__(self, client_id, redirect_uri, access_token=None, refresh_token=None, expiration_time=None):
        super().__init__(client_id, redirect_uri, access_token, refresh_token, expiration_time)

    def authenticate(self):
        challenges = self._generate_code()
        code_verifier = challenges[0]
        code_challenge = challenges[1]

        authorization_url = f"https://www.dropbox.com/oauth2/authorize?client_id={self.client_id}&response_type=code&code_challenge={code_challenge}&code_challenge_method=S256&token_access_type=offline"
        print("Step 1: Please visit this URL to authenticate:", authorization_url)
        code = input("Step 2: please input a code: ")
        url = "https://api.dropbox.com/oauth2/token"
        body = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
            "client_id": self.client_id,
        }

        base_time = datetime.datetime.now()
        # Todo: add error handling
        response = requests.post(url, body)

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
            url = "https://api.dropbox.com/oauth2/token"
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

    def upload_file(self, local_path, destination_path, __retry_count=0):
        url = "https://content.dropboxapi.com/2/files/upload"
        if self.token_alive() is False:
            if self.token_refresh() is False:
                print("stop uploading file as token expired and can't refresh.")
                return False
        common_header = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/octet-stream"}

        if os.path.exists(local_path):
            body = {
                "autorename": False,
                "mode": "overwrite",
                "mute": True,
                "path": destination_path,
                "strict_conflict": False,
            }

            header = {"Dropbox-API-Arg": json.dumps(body), **common_header}

            with open(local_path, "rb") as fp:
                data = fp.read()

            response = requests.post(url, data=data, headers=header)
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

    def upload_training_results(self, model_name, local_file_paths):
        if isinstance(local_file_paths, str):
            local_file_paths = [local_file_paths]

        for local_file_path in local_file_paths:
            file_name = os.path.basename(local_file_path)
            destination_path = f"/{model_name}/{file_name}"
            self.upload_file(local_file_path, destination_path)

    def download_file(self, destination_file_path, local_path_to_save, __retry_count=0):
        url = "https://content.dropboxapi.com/2/files/download"
        if self.token_alive() is False:
            if self.token_refresh() is False:
                print("stop downloading file as token expired and can't refresh.")
                return False
        common_header = {"Authorization": f"Bearer {self.access_token}"}
        local_path_dir = os.path.dirname(local_path_to_save)
        if os.path.exists(local_path_dir) is False:
            os.makedirs(local_path_dir)

        body = {
            "path": destination_file_path,
        }

        header = {"Dropbox-API-Arg": json.dumps(body), **common_header}

        response = requests.post(url, headers=header)
        if response.status_code == 200:
            with open(local_path_to_save, mode="w") as fp:
                fp.write(response.text)
            return local_path_to_save
        elif response.status_code == 401:
            self.token_refresh()
            return self.download_file(destination_file_path, local_path_to_save, __retry_count)
        else:
            print(f"Unkown error: {response.status_code}, {response.text}")
            if __retry_count < 3:
                time.sleep(3)
                return self.download_file(destination_file_path, local_path_to_save, __retry_count + 1)
            else:
                print("stop uploading files as it files several times.")
                return None
