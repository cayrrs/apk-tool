import requests
import subprocess
import os
import zipfile
import re

choices = ["1: github url\n", "2: apk file\n"]

def downloadfromurl(url, destination):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(destination, "wb") as file:
            file.write(response.content)
        print(f"download finished, source: {url}")
    except:
        print("download failed")


def extractzipfile(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zipref:
        zipref.extractall()


def init():
    if os.path.isdir("ADB"):
            print("found ADB")
            print("init finished")
    else:
            print("ADB not found, downloading")
            downloadfromurl(
                "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
                "adb.zip"
            )
            extractzipfile("adb.zip")
            os.remove("adb.zip")
            os.rename("platform-tools", "ADB")


def menu():
     os.system("cls")
     print("apk install method\n")
     for choice in choices:
          print(choice)
     select = input("\nselection: ")
     selection(int(select))


def selection(num):
     if num == 1:
          githuburl()
     elif num == 2:
          apkfile()
     else:
          print("input a valid number")
          os.system("cls")
          menu()



def githuburl():
     os.system("cls")
     print("github url method\n")
     url = input("paste the github release url: ")
     resp = requests.get(url, stream=True)
     resp.raise_for_status()

     cd = resp.headers.get("content-disposition")
     if cd:
          match = re.search(r'filename="?([^"]+)"?', cd)
          filename = match.group(1) if match else "downloaded.apk"
     else:
          filename = url.split("/")[-1]
     with open(filename, "wb") as f:
          for chunk in resp.iter_content(chunk_size=8192):
               if chunk:
                    f.write(chunk)
     print(f"saved {filename}")
     should = input(f"\ninstall {filename} y/n? ")
     if should in ["y", "yes", "yuh", "yup bro"]:
          print("starting install (make sure ur device is properly plugged in and you know adb should work)")
          installapk(filename)

def apkfile():
     os.system("cls")
     print("apk name method\n")
     print("make sure the apk file is in the same directory as this script.\n")
     dumbass = input("paste apk file name (with .apk)\n")
     installapk(dumbass)



def installapk(filename):
     basedir = os.path.dirname(os.path.abspath(__file__))
     adbpath = os.path.join(basedir, "ADB", "adb.exe")
     apkpath = os.path.join(basedir, filename)
     print(f"installing {filename}")
     try:
        result = subprocess.run([adbpath, "install", "-r", apkpath], capture_output=True, text=True, check=True)
        print(result.stdout)
        print("install completed")
     except subprocess.CalledProcessError as e:
          print("install failed: ")
          print(e.stderr)
          print(e.stdout)
        


init()
menu()