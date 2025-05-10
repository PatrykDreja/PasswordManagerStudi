import os
import ctypes

key_file = './key.key'
db_file = './baza_hasel.db'
config_file = './config.json'

def hide_file(file_path):
    if os.path.exists(file_path):
        ctypes.windll.kernel32.SetFileAttributesW(file_path, 2)

def unhide_file(file_path):
    if os.path.exists(file_path):
        ctypes.windll.kernel32.SetFileAttributesW(file_path, 0)

def hide_files():
    files_to_hide = [key_file, db_file, config_file]
    for file_path in files_to_hide:
        hide_file(file_path)

def unhide_files():
    files_to_unhide = [key_file, db_file, config_file]
    for file_path in files_to_unhide:
        unhide_file(file_path)
