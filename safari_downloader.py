# A resumable Safari Books Online Video downloader
# Main reference: https://mvdwoord.github.io/tools/2017/02/02/safari-downloader.html

from bs4 import BeautifulSoup
import requests
import os
import subprocess
import unicodedata
import string

import config
# Create a config.py file with the following content:
# class Config:
#     URL = 'https://learning.oreilly.com/videos/cisco-ccna/9781838646028'
#     OUTPUT_FOLDER = './output'
#     DOWNLOADER = '/usr/bin/youtube-dl'
# export cookies from logged in session, will work with individual or enterprise accounts alike
#     COOKIES = './cookies.txt'


class SafariDownloader:
    def __init__(self, url, output_folder, cookies, downloader_path='youtube-dl'):
        self.output_folder = output_folder
        self.downloader_path = downloader_path
        self.cookies = cookies

        req = requests.get(url)
        soup = BeautifulSoup(req.text, 'html.parser')
        self.topics = soup.find_all('li', class_='toc-level-1') # top-level topic titles

    def validify(self, filename, isdir=False):
        valid_chars = "-_. %s%s" % (string.ascii_letters, string.digits)
        if isdir:
            valid_chars = "-_./ %s%s" % (string.ascii_letters, string.digits)
        valid_chars = frozenset(valid_chars)
        # The unicodedata.normalize call replaces accented characters with the unaccented equivalent,
        # which is better than simply stripping them out. After that all disallowed characters are removed.
        cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        return ''.join(c for c in cleaned_filename if c in valid_chars).replace(':', '').replace(' ', '-')

    def download(self):
        for topic in self.topics:
            topic_name = topic.a.text
            # Creating folder to put the videos in
            save_folder = '{}/{}'.format(self.output_folder, topic_name)
            save_folder = self.validify(save_folder, True)
            os.makedirs(save_folder, exist_ok=True)
            for index, video in enumerate(topic.ol.find_all('a')):
                video_name = '{:03d}-{}'.format(index + 1, video.text)
                video_name = self.validify(video_name)
                video_url = video.get('href')
                video_out = '{}/{}.mp4'.format(save_folder, video_name)
                # Check if file already exists
                if os.path.isfile(video_out):
                    print("File {} already exists! Skipping...".format(video_out))
                    continue
                print("Downloading {} ...".format(video_name))

                #supported_formats = "best"
                supported_formats = "(mp4)[width=960][height=540]/(mp4)[width=966][height=540]/(mp4)[width=960][height=540]/(mp4)[width=854][height=480]/(mp4)[width=852][height=480]/(mp4)[width=720][height=540]"

                try:
                    subprocess.check_output([self.downloader_path, "--cookie", self.cookies, "--output", video_out, video_url, "--ignore-config", "-f", supported_formats, "--verbose"], stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    if e.output.decode("utf-8").find("requested format not available"):
                        # catch available formats and add to supported_formats string than re-run
                        subprocess.run([self.downloader_path, "--cookie", self.cookies, "--output", video_out, video_url, "--ignore-config", "-F"])


if __name__ == '__main__':
    app_config = config
    downloader = SafariDownloader(url=app_config.URL, output_folder=app_config.OUTPUT_FOLDER, cookies=app_config.COOKIES, downloader_path=app_config.DOWNLOADER)
    downloader.download()
