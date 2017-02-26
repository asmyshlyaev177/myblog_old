# -*- coding: utf-8 -*-
import os, datetime, json, re, shutil, random
from bs4 import BeautifulSoup
from PIL import Image
from django.utils.encoding import uri_to_iri, iri_to_uri
from moviepy.editor import *

src_szs = [480, 800, 1366, 1600, 1920]


def deleteThumb(text):
    # удаляем файлы картинок при удалении поста
    img_links = re.findall\
        (r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)\
         -(?P<res>\d{3,4})\.(?P<ext>\S*)", str(text))
    img_path = []
    for img in img_links:
        img_path.append(uri_to_iri('/root/myblog/myblog/blog/static/media/\
                                                {}/{}/{}/{}{}.{}'
                                   .format(img[0], img[1], img[2], img[3], "-" +
                                                 img[4], img[5])))
        img_path.append(uri_to_iri('/root/myblog/myblog/blog/static/media/\
                                                {}/{}/{}/{}.{}'
                                   .format(img[0], img[1], img[2], img[3],
                                                                    img[5])))
    for i in img_path:
        if os.path.isfile(i):
            os.remove(i)


def srcsetThumb(data, post_id=None):
    thumb = BeautifulSoup("html5lib").new_tag("img")
    thumb['src'] = "/" + str(data)
    if post_id:
        soup = srcsets(thumb, False, post_id=post_id)
    else:
        soup = srcsets(thumb, False)
    soup.html.unwrap()
    soup.head.unwrap()
    soup.body.unwrap()
    image_url = soup.prettify()
    return str(image_url)


def findLink(text):
    return re.search(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)\.(?P<ext>\w*)", str(text))


def findFile(link):
    if link:
        return '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}.{}'\
            .format(link.group("year"), link.group("month"), link.group("day"),
                                        link.group("file"), link.group("ext"))
    else:
        return ""


def saveImage(link, file, sz):

    file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.{}'\
                        .format(link.group("year"), link.group("month"),
                        link.group("day"), uri_to_iri(link.group("file")),
                        sz, link.group("ext"))

    link_out = '/media/{}/{}/{}/{}-{}.{}'\
            .format(link.group("year"), link.group("month"),
            link.group("day"), link.group("file"),
            sz, link.group("ext"))
    img = Image.open(file)
    sz_tuple = (sz, sz * 20)

    img.thumbnail(sz_tuple, Image.ANTIALIAS)
    img.save(file_out, subsampling=0, quality='keep')  # сохраняем
    return link_out


def srcsets(text, wrap_a, post_id=None):
    """Make few srcsets"""
    soup = BeautifulSoup(uri_to_iri(text), "html5lib")  # текст поста
    print("***************************")
    print('soup ', str(soup))

    # def not_processed_imgs(tag):
    #    return (tag.name == 'img' and
    #            'responsive-img' not in tag.get('class') and
    #            'responsive-img,' not in tag.get('class'))

    img_links_raw = soup.find_all("img")  # ищем все картинки
    #img_links_raw = soup.find_all(not_processed_imgs)
    print("***************************")
    print('img_links_raw ', str(img_links_raw))
    img_links = []
    for i in img_links_raw:  # фильтруем без srcset, ещё не обработанные
        # i['class'].remove('fr-dii fr-draggable')
        if not i.has_attr('srcset'):
            img_links.append(i)

    print("***************************")
    print('img_links ', str(img_links))
    if len(img_links) != 0:
        for i in img_links:  # для каждой
            srcset = {}
            notgif = False

            # находим ссылку и файл и вых. файл
            del i['style']  # удаляем стиль

            link = findLink(iri_to_uri(i))
            print("***************************")
            print('link ', str(link))
            file = uri_to_iri(findFile(link))
            print("***************************")
            print('file ', str(file))
            original_pic = '/media/{}/{}/{}/{}.{}'.\
                    format(link.group("year"), link.group("month"),
                    link.group("day"), uri_to_iri(link.group("file")),
                    link.group("ext"))

            print("***************************")
            print('original_pic ', str(original_pic))
            # сжимать пикчу! и удалять оригинальный файл

            if os.path.isfile(file):

                i['class'] = 'responsive-img post-image'
                # если картинка больше нужного размера создаём миниатюру
                w, h = Image.open(file).size
                ext = i['src'].split('.')[-1].lower()

                if ext == "gif":
                    notgif = False
                else:
                    notgif = True

                if notgif:
                    for sz in reversed(src_szs):
                        if w > sz:
                            srcset[sz] = saveImage(link, file, sz)

                    if 1600 in srcset:
                        alt = srcset[1366]   # дефолт
                        if 1920 not in srcset:
                            srcset[1920] = saveImage(link, file, 1920)
                            # проверка пуст ли элемент

                    elif 1366 in srcset:
                        if 1600 not in srcset:
                            srcset[1600] = saveImage(link, file, 1600)

                        alt = srcset[1366]

                    elif 800 in srcset:
                        if 1366 not in srcset:
                            srcset[1366] = saveImage(link, file, 1366)

                        alt = srcset[1366]

                    elif 480 in srcset:
                        alt = original_pic
                        if 800 not in srcset:
                            srcset[800] = saveImage(link, file, 800)

                    else:
                        alt = original_pic
                        if 480 not in srcset:
                            srcset[480] = original_pic

                    src_str = ""
                    for src in srcset.keys():
                        src_str += srcset[src] + " " + str(src) + "w, "

                    src_str = src_str.rstrip(', ')
                    print("***************************")
                    print('src_str ', str(src_str))
                    i['srcset'] = src_str
                    i['src'] = alt
                    i['sizes'] = "60vw"
                    # "(min-width: 40em) 33.3vw, 100vw"

                    """i['src'] = '/media/{}/{}/{}/{}-{}.{}'.\
                        format(link.group("year"), link.group("month"),\
                               link.group("day"),link.group("file"),alt,\
                               link.group("ext"))"""
                else:  # конвертим гифки в webm
                    file_out = "/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.webm"\
                    .format(link.group("year"), link.group("month"),
                        link.group("day"), link.group("file"), str(post_id))
                    link_out = '/media/{}/{}/{}/{}-{}.webm'\
                            .format(link.group("year"), link.group("month"),
                            link.group("day"), link.group("file"), str(post_id))

                    clip = VideoFileClip(file)
                    video = CompositeVideoClip([clip])
                    #video.write_videofile(file_out_tmp, codec='libvpx', audio=False,
                    #        ffmpeg_params=['-crf', '4', '-b:v', '1500K'])
                    # игнорирует параметры ffmpeg
                    video.write_videofile(uri_to_iri(file_out), codec='libvpx', audio=False,
                            preset='superslow')
                    os.remove(file)

                    webm = BeautifulSoup("", "html5lib").new_tag("video")
                    webm['autoplay'] = ""
                    webm['loop'] = ""
                    webm['controls'] = ""
                    webm['style'] = "max-width: " + str(w) + "px;"
                    source = BeautifulSoup("", "html5lib").new_tag("source")
                    source['src'] = link_out
                    source['type'] = "video/webm"
                    webm.insert(0, source)
                    i.replaceWith(webm)

                if wrap_a and notgif:
                    a_tag = soup.new_tag("a")
                    # оборачиваем в ссылку на оригинал
                    a_tag['href'] = original_pic
                    a_tag['data-gallery'] = ""
                    i = i.wrap(a_tag)
    return soup
