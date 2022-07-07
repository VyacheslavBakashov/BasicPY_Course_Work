import json
import requests
import time
from tqdm import tqdm


def define_date(seconds=None):
    return time.strftime('%d_%m_%Y', time.localtime(seconds))


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
