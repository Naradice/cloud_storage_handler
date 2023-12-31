import base64
import datetime
import hashlib
import os
import random
import string


class BaseHandler:
    def __init__(self, client_id, redirect_uri, access_token=None, refresh_token=None, expiration_time=None):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiration_time = expiration_time

    def _generate_code(self) -> tuple[str, str]:
        rand = random.SystemRandom()
        code_verifier = "".join(rand.choices(string.ascii_letters + string.digits, k=128))

        code_sha_256 = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        b64 = base64.urlsafe_b64encode(code_sha_256)
        code_challenge = b64.decode("utf-8").replace("=", "")

        return (code_verifier, code_challenge)

    def token_alive(self):
        current_time = datetime.datetime.now()

        if self.expiration_time is None or current_time > self.expiration_time:
            return False
        return True

    def authenticate(self):
        pass

    def token_refresh(self):
        pass

    def upload_file(self, local_path, destination_path, __retry_count=0):
        pass

    def upload_training_results(self, model_name, local_file_paths):
        if isinstance(local_file_paths, str):
            local_file_paths = [local_file_paths]

        for local_file_path in local_file_paths:
            file_name = os.path.basename(local_file_path)
            destination_path = f"/{model_name}/{file_name}"
            self.upload_file(local_file_path, destination_path)

    def download_file(self, destination_file_path, local_path_to_save, __retry_count=0):
        pass
