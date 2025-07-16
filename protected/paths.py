import os
import platform

def get_data_folder():
    if platform.system() == "Windows":
        return os.path.join(os.environ["APPDATA"], "PasswordManager")
    elif platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Application Support/PasswordManager")
    else:  # Linux
        return os.path.expanduser("~/.config/PasswordManager")

def get_local_path(filename):
    folder = get_data_folder()
    if not os.path.exists(folder):
        os.makedirs(folder)
    return os.path.join(folder, filename)
