import os
import shutil

from ..handler import BaseHandler


class ColaboHandler(BaseHandler):
    def __init__(
        self,
        mount_path,
        gdrive_path,
    ):
        try:
            from google.colab import drive
        except ImportError:
            raise Exception("You can't use this handler outside of colaboratory")
        except Exception as e:
            print(f"unkwon import error happened: {e}")
        # Since Colabo module handle tokens inside the module and the notebook env, we don't need to handle them
        super().__init__(None, None, None, None, None)
        self.mount_path = mount_path
        self.log_folder_path = os.path.join(mount_path, gdrive_path)

    def authenticate(self):
        drive.mount(self.mount_path)
        if os.path.exists(self.log_folder_path) is False:
            os.makedirs(self.log_folder_path)

    def upload_file(self, local_path, destination_path, __retry_count=0):
        try:
            shutil.copy(local_path, destination_path, dirs_exist_ok=True)
        except Exception as e:
            self.authenticate()
            if __retry_count < 3:
                self.upload_file(local_path, destination_path, __retry_count + 1)
            else:
                print(f"failed to copy {local_path} to {destination_path} due to {e}")

    def upload_training_results(self, model_name, local_file_paths):
        destination_base_path = f"{self.log_folder_path}/{model_name}"
        if isinstance(local_file_paths, str):
            local_file_paths = [local_file_paths]

        for local_file_path in local_file_paths:
            file_name = os.path.basename(local_file_path)
            destination_path = f"/{destination_base_path}/{file_name}"
            self.upload_file(local_file_path, destination_path)

    def download_file(self, destination_file_path, local_path_to_save, __retry_count=0):
        try:
            shutil.copy(local_path_to_save, destination_file_path, dirs_exist_ok=True)
        except Exception as e:
            self.authenticate()
            if __retry_count < 3:
                self.upload_file(local_path_to_save, destination_file_path, __retry_count + 1)
            else:
                print(f"failed to copy {local_path_to_save} to {destination_file_path} due to {e}")
