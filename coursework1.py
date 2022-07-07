from VkUser import VkUser
from YaUploader import YaUploader


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
