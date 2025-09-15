import os
import gzip
import requests
import pandas as pd
import json
import sys
import subprocess

# global variables 
base_url = 'https://deb.debian.org/debian/'
repo_website = base_url + 'dists/stable/main/binary-amd64/Packages.gz'
download_path = 'Downloaded_packages'


def get_package():
    compressed_repo = requests.get(repo_website)

    with open("Packages.gz",'wb') as f:
        f.write(compressed_repo.content)


def parse_package():
    # extract the packages the from the gz extension
    with gzip.open('Packages.gz', 'rt') as f:
        file_content = f.read()

    return file_content

import pandas as pd
import json

def store_info(file_content, to_json, json_file="packages.json"):
    packages = []

    blocks = file_content.strip().split("\n\n")

    for block in blocks:
        info = {
            'package_name': '',
            'version': '',
            'description': '',
            'size': '',
            'file_location': '',
            'md5-hash': '',
            'sha256': ''
        }

        for line in block.splitlines():
            if line.startswith("Package:"):
                info['package_name'] = line.split(":", 1)[1].strip()
            elif line.startswith("Version:"):
                info['version'] = line.split(":", 1)[1].strip()
            elif line.startswith("Description:"):
                info['description'] = line.split(":", 1)[1].strip()
            elif line.startswith("MD5sum:"):
                info['md5-hash'] = line.split(":", 1)[1].strip()
            elif line.startswith("SHA256:"):
                info['sha256'] = line.split(":", 1)[1].strip()
            elif line.startswith("Filename:"):
                info['file_location'] = line.split(":", 1)[1].strip()
            elif line.startswith("Installed-Size:"):
                info['size'] = line.split(":", 1)[1].strip()

        if info['package_name']:
            packages.append(info)

    df = pd.DataFrame(packages)

    if to_json:
        with open(json_file, "w") as f:
            json.dump(packages, f, indent=4)
    
    os.remove('Packages.gz')

    return df 

def check_if_installed(dataframe, user_packages):
    available_packages = []
    for i in user_packages:
        try:
            subprocess.run(
                ['dpkg', '-s', i],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            print(f' Package {i} is already installed on your system.')

        except subprocess.CalledProcessError:
            if i in dataframe['package_name'].values:
                row = dataframe[dataframe['package_name'] == i].iloc[0].to_dict()
                available_packages.append(row)
            else:
                print(f' Package {i} cannot be found in the repo database.')

    return available_packages

def download_packages(available_packages):
    if not os.path.exists(download_path):
        os.mkdir(download_path)

    for i in available_packages:
        package_url = base_url + i['file_location']
        r = requests.get(package_url)
        file_name = os.path.join (download_path, os.path.basename(i['file_location']))


        with open(file_name,'wb') as f:
            f.write(r.content)

def main():
    n = len(sys.argv)
    if n <= 1 : 
        print('''
            This is a custom package manager using dpkg , and only works on the debian and ubuntu systens . 
            To install a package use -> python main.py packages...
                         ''') 
        sys.exit(1)

    user_packages = sys.argv[1:]
    get_package()
    file_content = parse_package()
    package_frame = store_info(file_content, to_json=False) # to store json or not is the boolean
    available_packages = check_if_installed(package_frame,user_packages)
    download_packages(available_packages)





if __name__ == '__main__':
    main()