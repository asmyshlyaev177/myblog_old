# -*- coding: utf-8 -*-
import os, datetime, json, re
from slugify import slugify, SLUG_OK
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
import datetime
from urllib.request import urlopen, urlretrieve, Request
from django.utils.encoding import uri_to_iri, iri_to_uri
from time import gmtime, strftime

src_szs = [480, 800, 1366, 1600, 1920]

def deleteThumb(text):
    # удаляем файлы картинок при удалении поста
    img_links = re.findall\
        (r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)-(?P<res>\d{3,4})\.(?P<ext>\S*)"\
        ,str(text))
    img_path = []
    for img in img_links:
        img_path.append(uri_to_iri('/root/myblog/myblog/blog/static/media/{}/{}/{}/{}{}.{}'\
                                   .format(img[0], img[1],img[2],img[3],"-"+img[4],img[5])))
        img_path.append(uri_to_iri('/root/myblog/myblog/blog/static/media/{}/{}/{}/{}.{}'\
                                   .format(img[0], img[1],img[2],img[3],img[5])))
    for i in img_path:
        if os.path.isfile(i):
            os.remove(i)

def srcsetThumb(data):
    thumb = BeautifulSoup("lxml").new_tag("img")
    thumb['src'] = "/"+str(data)
    soup = srcsets(thumb, False)
    soup.html.unwrap()
    #soup.head.unwrap()
    soup.body.unwrap()
    image_url = soup.prettify()
    return str(image_url)

def findLink(text):
    return re.search(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*)\.(?P<ext>\w*)", str(text))

def findFile(link):
    if link:
        return '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}.{}'\
    .format(link.group("year"), link.group("month"),link.group("day"),\
            link.group("file"),link.group("ext"))
    else:
        return ""

def saveImage(link, file, sz, blank=False):
    if blank:
        file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-blank-{}.{}'\
        .format(link.group("year"), link.group("month"),\
                link.group("day"),uri_to_iri(link.group("file")),\
                sz, link.group("ext"))
        link_out = '/media/{}/{}/{}/{}-blank-{}.{}'\
        .format(link.group("year"), link.group("month")\
                ,link.group("day"),link.group("file"),\
                sz, link.group("ext"))
    else:
        file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.{}'\
        .format(link.group("year"), link.group("month"),\
                link.group("day"),uri_to_iri(link.group("file")),\
                sz, link.group("ext"))
        link_out = '/media/{}/{}/{}/{}-{}.{}'\
        .format(link.group("year"), link.group("month")\
                ,link.group("day"),link.group("file"),\
                sz, link.group("ext"))
    img = Image.open(file)
    sz_tuple = (sz, sz*20)

    if blank:
        img.paste('#03a9f4', None)
        img.save(file_out, optimize=True, quality=1)
    else:
        img.thumbnail(sz_tuple, Image.ANTIALIAS)
        img.save(file_out, subsampling=0, quality='keep') # сохраняем
    return link_out


def srcsets(text, wrap_a):
    """Make few srcsets"""
    soup = BeautifulSoup(uri_to_iri(text), "lxml") #текст поста
    print("***************************")
    print('soup ', str(soup))
    img_links_raw = soup.find_all("img") #ищем все картинки
    print("***************************")
    print('img_links_raw ', str(img_links_raw))
    img_links = []
    for i in img_links_raw: #фильтруем без srcset, ещё не обработанные
        if not i.has_attr('srcset'):
            img_links.append(i)

    print("***************************")
    print('img_links ', str(img_links))
    if len(img_links) != 0:
        for i in img_links: # для каждой
            srcset = {}
            srcset_blank = {}
            notgif = False

            # находим ссылку и файл и вых. файл
            del i['style'] #удаляем стиль

            link = findLink(iri_to_uri(i))
            print("***************************")
            print('link ', str(link))
            file = uri_to_iri(findFile(link))
            print("***************************")
            print('file ', str(file))
            original_pic = '/media/{}/{}/{}/{}.{}'.\
            format(link.group("year"), link.group("month"),\
                   link.group("day"),uri_to_iri(link.group("file")),\
                   link.group("ext"))

            print("***************************")
            print('original_pic ', str(original_pic))
            # сжимать пикчу! и удалять оригинальный файл

            if os.path.isfile(file):

                i['class'] = 'responsive-img'
                # если картинка больше нужного размера создаём миниатюру
                w,h = Image.open(file).size
                original_pic_blank = saveImage(link, file,
                                             w, blank=True )
                print("***************************")
                print('original_pic_blank ', str(original_pic_blank))
                ext = i['src'].split('.')[-1].lower()

                if ext == "jpg" or ext == "jpeg" or ext == "bmp" or ext == "png":
                    notgif = True

                if notgif:
                    for sz in reversed(src_szs):
                        if w > sz:
                            srcset[sz] = saveImage(link, file, sz )
                            srcset_blank[sz] = saveImage(link, file,
                                                         sz, blank=True )


                    if 1600 in srcset:
                        alt = srcset[1366]   #дефолт
                        alt_blank = srcset_blank[1366]   #дефолт
                        if 1920 not in srcset :
                            srcset[1920] = saveImage(link, file, 1920  ) #проверка пуст ли элемент
                            srcset_blank[1920] = saveImage(link, file,
                                                         1920, blank=True )
                    elif 1366 in srcset:
                        if 1600 not in srcset :
                            srcset[1600] = saveImage(link, file, 1600 )
                            srcset_blank[1600] = saveImage(link, file,
                                                         1600, blank=True )
                        alt = srcset[1366]
                        alt_blank = srcset_blank[1366]   #дефолт
                    elif 800 in srcset:
                        if 1366 not in srcset :
                            srcset[1366] = saveImage(link, file, 1366)
                            srcset_blank[1366] = saveImage(link, file,
                                                         1366, blank=True )
                        alt = srcset[1366]
                        alt_blank = srcset_blank[1366]   #дефолт
                    elif 480 in srcset:
                        alt = original_pic
                        alt_blank = original_pic_blank
                        if 800 not in srcset :
                            srcset[800] = saveImage(link, file, 800)
                            srcset_blank[800] = saveImage(link, file,
                                                         800, blank=True )
                    else:
                        alt = original_pic
                        alt_blank = original_pic_blank
                        if 480 not in srcset :
                            srcset[480] = original_pic
                            srcset_blank[480] = original_pic_blank

                    src_str=""
                    src_str_blank=""
                    for src in srcset.keys():
                        src_str +=srcset[src] + " "+str(src)+"w, "
                        src_str_blank +=srcset_blank[src] + " "+str(src)+"w, "

                    print("***************************")
                    print('src_str ', str(src_str))
                    print("***************************")
                    print('src_str_blank ', str(src_str_blank))
                    src_str = src_str.rstrip(', ')
                    src_str_blank = src_str_blank.rstrip(', ')
                    i['srcset'] = src_str_blank
                    i['srcset_real'] = src_str

                    i['src'] = alt_blank
                    i['src_real'] = alt
                    i['sizes'] =  "60vw"
                    # "(min-width: 40em) 33.3vw, 100vw"

                    """i['src'] = '/media/{}/{}/{}/{}-{}.{}'.\
                        format(link.group("year"), link.group("month"),\
                               link.group("day"),link.group("file"),alt,\
                               link.group("ext"))"""
                if wrap_a and notgif:
                    a_tag = soup.new_tag("a")
                    # оборачиваем в ссылку на оригинал
                    a_tag['href'] = original_pic
                    a_tag['data-gallery'] = ""
                    i = i.wrap(a_tag)
    return soup
