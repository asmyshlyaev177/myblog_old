import os
import re
from PIL import Image
from bs4 import BeautifulSoup
from django.utils.encoding import uri_to_iri, iri_to_uri
from moviepy.editor import *

src_szs = [480, 800, 1366, 1600, 1920]


def validate_post_image(value):
    """ 
    Проверка что загружаемая картинка разрешенного типа
    принимает аргументом ссылку или путь к файлу
    """
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpeg', '.jpg', '.bmp', '.png', '.tiff', '.gif', '.webm']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


def delete_thumb(text):
    """
    удаляем картинки при удалении поста 
    """
    img_links = \
        re.findall \
            (r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)-(?P<res>\d{3,4})\.(?P<ext>\S*)",
             str(text))
    img_path = []
    # ищем полные пути до картинок
    for img in img_links:
        img_path.append(uri_to_iri('/root/myblog/myblog/blog/static/media/\
                                                {}/{}/{}/{}{}.{}'
                                   .format(img[0], img[1], img[2], img[3], "-" +
                                           img[4], img[5])))
        img_path.append(uri_to_iri('/root/myblog/myblog/blog/static/media/\
                                                {}/{}/{}/{}.{}'
                                   .format(img[0], img[1], img[2], img[3],
                                           img[5])))
    for img in img_path:
        if os.path.isfile(img):
            os.remove(img)


def clean_tags_from_soup(soup):
    """
    Удаляем лишние тэги когда нужен только фрагмент HTMl кода
    """
    soup.html.unwrap()
    soup.head.unwrap()
    soup.body.unwrap()
    return soup.prettify()


def srcset_thumb(data, post_id=None):
    """ 
    Конвертим картинки для главной страницы
    Принимает ссылку на файл и отдаёт готовый html код
    """
    thumb = BeautifulSoup("html5lib").new_tag("img")
    thumb['src'] = "/" + str(data)
    if post_id:
        soup = make_srcsets(thumb, False, post_id=post_id)
    else:
        soup = make_srcsets(thumb, False)
    image_url = clean_tags_from_soup(soup)
    return str(image_url)


def find_link(text):
    """
    Парсим ссылку на файл
    """
    return re.search(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)\.(?P<ext>\w*)", str(text))


def find_file(link):
    """
    Парсим ссылку на файл и возвращаем полный путь до него
    """
    if link:
        return '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}.{}' \
            .format(link.group("year"), link.group("month"), link.group("day"),
                    link.group("file"), link.group("ext"))
    else:
        return ""


def save_image(link, file, w, h=3500):
    """
    Сохраняем файл из ссылки, возвращает сслыку на картинку
    """

    file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.{}' \
        .format(link.group("year"), link.group("month"),
                link.group("day"), uri_to_iri(link.group("file")),
                w, link.group("ext"))

    link_out = '/media/{}/{}/{}/{}-{}.{}' \
        .format(link.group("year"), link.group("month"),
                link.group("day"), link.group("file"),
                w, link.group("ext"))
    img = Image.open(file)
    sz_tuple = (w, h)

    img.thumbnail(sz_tuple, Image.ANTIALIAS)
    img.save(file_out, subsampling=0, quality=85)  # сохраняем
    return link_out


def convert_img_to_srcset(link, file, original_pic, src_szs):
    """
    Если картинка больше нужного размера создаём миниатюру
    """
    srcset = {}
    w, h = Image.open(file).size

    for size in reversed(src_szs):
        if w > size:
            srcset[size] = save_image(link, file, size)

    if 1600 in srcset:
        alt = srcset[1366]  # дефолт img src
        if 1920 not in srcset:  # проверка пуст ли элемент
            srcset[1920] = save_image(link, file, 1920)

    elif 1366 in srcset:
        alt = srcset[1366]
        if 1600 not in srcset:
            srcset[1600] = save_image(link, file, 1600)

    elif 800 in srcset:
        if 1366 not in srcset:
            srcset[1366] = save_image(link, file, 1366)
        alt = srcset[1366]

    elif 480 in srcset:
        alt = original_pic
        if 800 not in srcset:
            srcset[800] = save_image(link, file, 800)

    else:
        alt = original_pic
        if 480 not in srcset:
            srcset[480] = original_pic

    src_str = ""
    for src in srcset.keys():
        src_str += srcset[src] + " " + str(src) + "w, "

    src_str = src_str.rstrip(', ')

    return src_str, alt


def convert_gif_to_webm(link, file, ext, post_id):
    """
    Конвертим гифки в webm
    """
    clip = VideoFileClip(file)
    w, h = clip.size
    webm = BeautifulSoup("", "html5lib").new_tag("video")
    webm['autoplay'] = ""
    webm['loop'] = ""
    webm['controls'] = ""
    webm['style'] = "max-width: " + str(w) + "px;"
    source = BeautifulSoup("", "html5lib").new_tag("source")
    if ext == "webm":
        source['src'] = "/media" + link.group()
    else:
        file_out = uri_to_iri("/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.webm"
                              .format(link.group("year"), link.group("month"),
                                      link.group("day"), link.group("file"), str(post_id)))
        link_out = uri_to_iri('/media/{}/{}/{}/{}-{}.webm'
                              .format(link.group("year"), link.group("month"),
                                      link.group("day"), link.group("file"), str(post_id)))

        clip = VideoFileClip(file)
        video = CompositeVideoClip([clip])
        video.write_videofile(file_out, codec='libvpx',
                              audio=False, preset='superslow')

        source['src'] = link_out
    source['type'] = "video/webm"
    webm.insert(0, source)

    return webm


def find_img(soup):
    """
    Ищем все картинки в супе
    Возвращает лист БС тэгов
    """
    img_links_raw = soup.find_all("img")
    img_links = []
    for img in img_links_raw:  # фильтруем без srcset, ещё не обработанные
        if not img.has_attr('srcset'):
            img_links.append(img)
    return img_links


def make_srcsets(text, wrap_a, post_id=None):
    """
    Создаём srcsetы из картинок
    Аргументы:
    Принимает текст поста, оборачивать ли картинку в ссылку и опционально id поста
    Возвращает готовый html код
    """
    soup = BeautifulSoup(uri_to_iri(text), "html5lib")  # текст поста

    img_links = find_img(soup)

    if len(img_links) != 0:
        for img in img_links:
            # находим ссылку, файл и вых. файл
            del img['style']  # удаляем стиль

            link = find_link(iri_to_uri(img))
            file = uri_to_iri(find_file(link))
            original_pic = uri_to_iri('/media/{}/{}/{}/{}.{}'.
                                      format(link.group("year"), link.group("month"),
                                             link.group("day"), link.group("file"),
                                             link.group("ext")))

            if os.path.isfile(file):

                img['class'] = 'responsive-img post-image'
                ext = img['src'].split('.')[-1].lower()

                if ext == "gif" or ext == "webm":
                    webm = convert_gif_to_webm(link, file, ext, post_id)
                    img.replaceWith(webm)
                    # if ext == "gif":
                    #    os.remove(file)
                else:
                    # если картинка больше нужного размера создаём миниатюру
                    srcset, alt = convert_img_to_srcset(link, file, original_pic, src_szs)
                    img['srcset'] = srcset
                    img['src'] = alt
                    img['sizes'] = "60vw"

                    if wrap_a:
                        a_tag = soup.new_tag("a")
                        # оборачиваем в ссылку на оригинал
                        a_tag['href'] = original_pic
                        a_tag['data-gallery'] = ""
                        # img = img.wrap(a_tag)

    return soup


def strip_media_from_path(file):
    """
    Удаляем "media/" из путей к файлам
    """
    if re.search(r"^/media/", file):
        path = file.split(os.sep)[2:]
        new_path = ""
        for i in path:
            new_path = os.path.join(new_path, i)
        return uri_to_iri(new_path)
    else:
        return uri_to_iri(file)
