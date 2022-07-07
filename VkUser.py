import requests
import time


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
