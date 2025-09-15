import os
import gzip
import requests


# global variables 
base_url = 'https://deb.debian.org/debian/'
repo_website = base_url + 'dists/stable/main/binary-amd64/Packages.gz'


def get_package():
    compressed_repo = requests.get(repo_website)

    with open("Packages.gz",'wb') as f:
        f.write(compressed_repo.content)


def main():
    get_package()

if __name__ == '__main__':
    main()