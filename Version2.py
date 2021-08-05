from pprint import pprint
import requests
from datetime import datetime
import time
from tqdm import tqdm
import sys


with open('VK_token.txt', 'r') as file_object:
    vk_token = file_object.read().strip()

with open('YD_token.txt', 'r') as file_object:
    yd_token = file_object.read().strip()


class VKUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, vk_token, version):
        self.token = vk_token
        self.version = version
        self.params = {
            'access_token': self.token,
            'v': self.version
        }

    def get_user_id(self, version,q):
        search_url = self.url + 'users.search'
        self.token = vk_token
        self.version = version
        params = {
            'q': q
        }
        res = requests.get(search_url, params={**self.params, **params})
        return res.json()

    def input_params(self):
        input_step_1 = input('Выберите тип идентификатора: Имя = A, ID = B: ')
        if input_step_1 == 'B':
            vk_id = int(input('Введите id пользователя: '))
            return vk_id
        elif input_step_1 == 'A':
            res = input('Введите имя пользователя: ')
            vk_id = vk_client.get_user_id('5.130', res)['response']['items'][0]['id']
            return vk_id
        else:
            pprint('Введите корректную опцию')
            sys.exit()

    def check_vk_id(self):
        search_url = self.url + 'users.get'
        self.token = vk_token
        params = {
            'user_ids': vk_id
        }
        res = requests.get(search_url, params={**self.params, **params}).json()['response'][0]['is_closed']
        if res == False:
            pass
        else:
            pprint('Профиль данного пользователя закрыт')
            sys.exit()

    def get_all_photos(self):
        photos_url = self.url + 'photos.get'
        params = {
            'owner_id': vk_id,
            'count': count,
            'album_id': 'profile',
            'rev': 1,
            'extended': 1,
            'photos': 1,
        }
        res = requests.get(photos_url, params={**self.params, **params})
        return res.json()

    def get_photos_list(self):
        photos = self.get_all_photos()['response']['items']
        for photo in photos:
            photo_dict = {}
            url = photo['sizes'][-1]['url']
            photo_dict['size'] = photo['sizes'][-1]['type']
            photo_dict['url'] = url
            photo_dict['likes'] = photo['likes']['count']
            photo_dict['date'] = datetime.utcfromtimestamp(int(photo['date'])).strftime('%Y-%m-%d %H-%M-%S')
            photo_dict['file_name'] = f'{photo_dict["likes"]}_{photo_dict["date"]}'
            url_list.append(photo_dict)


class YaUploader:
    def __init__(self, yd_token):
        self.token = yd_token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def check_folder(self):
        folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': f'VK_photos_from_{vk_id}_profile'}
        response = requests.get(folder_url, headers=headers, params=params)
        print(response.status_code)
        if response.status_code != 200:
            self.create_folder()

    def create_folder(self):
        folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': f'VK_photos_from_{vk_id}_profile'}
        response = requests.put(folder_url, headers=headers, params=params)
        response.raise_for_status()
        if response.status_code == 201:
            print("Success")

    def get_upload_link(self, disk_file_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {
            'path': disk_file_path,
            'overwrite': 'true'
        }
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload_file_to_disk(self, disk_file_path, file):
        href = self.get_upload_link(disk_file_path=disk_file_path).get('href', '')
        response = requests.put(href, file)
        response.raise_for_status()


if __name__ == '__main__':
    vk_client = VKUser(vk_token, '5.130')
    url_list = []
    vk_id = vk_client.input_params()
    vk_client.check_vk_id()
    count = int(input('Введите кол-во фото для загрузки: '))

    vk_client.get_photos_list()
    uploader = YaUploader(yd_token)
    uploader.check_folder()

    for photo in tqdm(url_list):
        filename = photo['file_name']
        res = requests.get(photo['url']).content
        uploader.upload_file_to_disk(f'VK_photos_from_{vk_id}_profile/{filename}.jpg', res)
        time.sleep(0.005)
