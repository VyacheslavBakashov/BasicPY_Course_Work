import requests
# from pprint import pprint
import time
from tqdm import tqdm
import json


def define_date(seconds=None):
    return time.strftime('%d_%m_%Y', time.localtime(seconds))


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token_vk: str, version):
        self.token_vk = token_vk
        self.params = {
            'access_token': self.token_vk,
            'v': version
        }

    def check_id(self, owner_id: str):
        """
        Позволяет использовать как Screen_Name так и ID VK_user
        """
        if not owner_id.isdigit():
            check_id_url = self.url + 'utils.resolveScreenName'
            check_id_params = {'screen_name': owner_id}
            response = requests.get(check_id_url,  params={**self.params, **check_id_params})
            response.raise_for_status()
            owner_id = response.json()['response']['object_id']
        return owner_id

    def get_photos(self, owner_id, album_id='-6', count='5'):
        """
        Метод получает ссылки на фото в альбоме пользователя VK, их размер и название будущего файла

        :param owner_id: id или screen_name профиля VK, откуда будут выгружаться фото;
        :param album_id: id альбома, по умолчанию альбом с аватарками;
        :param count: число фотографий, которые будут выгружены, по умолчанию 5
        :return: список словарей с ключами 'url', 'size', 'file_name'
        """
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'owner_id': self.check_id(owner_id),
            'album_id': album_id,
            'photo_sizes': 1,
            'count': count,
            'extended': 1
        }
        resp = requests.get(get_photos_url, params={**self.params, **get_photos_params})
        resp.raise_for_status()
        if resp.status_code == 200:
            print(f'Успех! Из профиля получено {min(int(count), resp.json()["response"]["count"])} фотографии.\n')

        def _find_max_size(sizes_list):
            sizes = ('s', 'm', 'x', 'o', 'p', 'q', 'r', 'y', 'z', 'w')
            temp = max(sizes_list, key=lambda x: sizes.index(x['type']))
            return {'url': temp['url'], 'size': temp['type']}

        photos_list, likes_list_temp, dates_list_temp = [], [], []
        for photo in resp.json()['response']['items']:
            photo_dict = {}
            photo_dict.update(_find_max_size(photo['sizes']))
            likes_num, date = photo['likes']['count'], define_date(photo['date'])
            file_name = f"{likes_num}.jpg"
            if likes_num in likes_list_temp:
                file_name = f"{likes_num}_{define_date(photo['date'])}.jpg"
                if date in dates_list_temp and dates_list_temp.count(date) != 0:
                    file_name = f"{file_name.strip('.jpg')}_({dates_list_temp.count(date)}).jpg"
                dates_list_temp.append(date)
            likes_list_temp.append(likes_num)
            photo_dict['file_name'] = file_name
            photos_list.append(photo_dict)
        return photos_list

    def get_albums(self, owner_id: str):
        """
        Возвращает id доступных альбомов, их названия и кол-во фото в них

        :param owner_id: id профиля VK,
        :return: словарь, где ключи - id доступных альбомов, значения - названия, кол-во фото
        """
        get_albums_url = self.url + 'photos.getAlbums'
        get_albums_params = {'owner_id': owner_id, 'need_system': 1}
        resp = requests.get(get_albums_url, params={**self.params, **get_albums_params}).json()['response']['items']
        return {i['id']: [i['title'], i['size']] for i in resp}


class YaUploader:
    url = 'https://cloud-api.yandex.net/v1/disk/'

    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}',
            'Accept': 'application/json'
         }

    def create_folder(self, fldr_name: str):
        params_folder = {'path': f'{fldr_name}'}
        headers = self.get_headers()
        create_folder_url = f'{self.url}resources'
        response = requests.put(create_folder_url, params=params_folder, headers=headers)
        if response.status_code == 201:
            print(f'Создан каталог на Ya Disk: "{params_folder["path"]}/"\n'
                  f'Файлы будут загружены в созданный каталог.\n')
        elif response.status_code == 409:
            print(f'Так как указанный каталог "{params_folder["path"]}/" уже существует на Ya Disk,\n'
                  f'Файлы будут загружены в него же.\n')
        else:
            response.raise_for_status()

    def upload(self, photos_list: list, ya_folder_name=f'backup_{define_date()}', out_file='uploaded_files.json'):
        """
        Метод для загрузки фотографий на Yandex Disk из VK по ссылкам

        :param out_file: JSON файл со списком загруженных на Yandex Disk фото, по умолчанию 'uploaded_files.json'
        :param photos_list: список словарей, полученный с помощью VkUser.get_photos()
        :param ya_folder_name: имя папки, в которую будет сохранено, по умолчанию "backup_текущая_дата"
        :return: загружает фото на Ya Disk и создаёт JSON файл (out_file)
        """
        self.create_folder(ya_folder_name)
        disk_url = f'{self.url}resources/upload'
        headers = self.get_headers()
        for photo in tqdm(photos_list, desc='Загрузка файлов на Yandex Disk:'):
            url = photo.pop('url')
            params_upload = {
                'url': url,
                'path': f"{ya_folder_name}/{photo['file_name']}",
                'disable_redirects': False
            }
            response = requests.post(disk_url, params=params_upload, headers=headers)
            response.raise_for_status()
            # time.sleep(0.01)
        with open(out_file, 'w', encoding='utf-8') as output_file:
            json.dump(photos_list, output_file, indent=2)


if __name__ == '__main__':
    token_vk_file, token_ya_file = 'vk_token.txt', 'ya_token.txt'
    ver_api_vk = '5.131'

    id_ = input('Введите ID или Screen_Name профиля VK: ')
    folder_name = input('Введите имя папки, в которую будут скачаны фото: ')

    with open(token_vk_file, 'r') as file:
        token_vk_ = file.readline().strip()
    with open(token_ya_file, 'r') as file:
        token_ya_ = file.readline().strip()

    me = VkUser(token_vk_, ver_api_vk)
    my_ya_disk = YaUploader(token_ya_)

    # вторым и третьим аргументом можно передать id альбома и кол-во фото соответственно
    vk_photos_list = me.get_photos(id_)
    
    my_ya_disk.upload(vk_photos_list, folder_name)
