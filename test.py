
import os
def open_folder(path):
    openpath = 'start explorer '
    openpath = openpath + path
    os.system(openpath)

open_folder(".\\data\\video")
