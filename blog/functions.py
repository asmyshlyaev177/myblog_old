import os, datetime, json, re
from slugify import slugify, SLUG_OK
from bs4 import BeautifulSoup
from PIL import Image
from urllib.parse import urlparse, urlencode
import datetime
from urllib.request import urlopen, urlretrieve, Request
from django.utils.encoding import uri_to_iri, iri_to_uri
from time import gmtime, strftime

def deleteThumb(text):
	# удаляем файлы картинок при удалении поста
	img_links = re.findall\
		(r"/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<file>\S*.jpg)", str(text))
	for img in img_links:
		img_path = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}'.format(img[0], img[1],img[2],img[3])
		if os.path.isfile(img_path):
			os.remove(img_path)

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

def srcsets(text, wrap_a):
    """Make few srcsets"""
    soup = BeautifulSoup(uri_to_iri(text), "lxml") #текст поста
    img_links = soup.find_all("img") #ищем все картинки
    src_szs = [480, 800, 1366, 1600, 1920]


    if len(img_links) != 0:
        for i in img_links: # для каждой
            srcset = {}
            notgif = False

            # находим ссылку и файл и вых. файл
            del i['style'] #удаляем стиль
            link = findLink(iri_to_uri(i))
            file = uri_to_iri(findFile(link))

            #file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-thumbnail.{}'\
            #.format(link.group("year"), link.group("month"),link.group("day"),link.group("file"), link.group("ext"))

            if os.path.isfile(file):

                i['class'] = 'responsive-img'
                # если картинка больше нужного размера создаём миниатюру
                w,h = Image.open(file).size
                ext = i['src'].split('.')[-1].lower()

                if ext == "jpg" or ext == "jpeg" or ext == "bmp" or ext == "png":
                    notgif = True

                if notgif:
                    for sz in reversed(src_szs):
                        if w > sz:
                            file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.{}'\
                                .format(link.group("year"), link.group("month"),\
								link.group("day"),uri_to_iri(link.group("file")),\
                                sz, link.group("ext"))
                            link_out = '/media/{}/{}/{}/{}-{}.{}'\
                                .format(link.group("year"), link.group("month")\
								,link.group("day"),link.group("file"),\
                                sz, link.group("ext"))
                            srcset[sz] = link_out
                            img = Image.open(file)
                            sz_tuple = (sz, sz*10)
                            img.thumbnail(sz_tuple)
                            img.save(file_out) # сохраняем

                    src_str=""
                    for src in srcset.keys():
                        src_str +=srcset[src] + " "+str(src)+"w, "
                    src_str = src_str.rstrip(', ')
                    i['srcset'] = src_str

                    if 1366 in srcset:
                        alt = srcset[1366]
                    elif 800 in srcset:
                        alt = srcset[800]
                    elif 480 in srcset:
                        alt = srcset[480]
                    else:
                        alt = ""

                    i['src'] = alt
                    i['sizes'] =  "60vw"
					# "(min-width: 40em) 33.3vw, 100vw"

                    """i['src'] = '/media/{}/{}/{}/{}-{}.{}'.\
                        format(link.group("year"), link.group("month"),\
                               link.group("day"),link.group("file"),alt,\
                               link.group("ext"))"""
                if wrap_a and notgif:
                    a_tag = soup.new_tag("a")
                    # оборачиваем в ссылку на оригинал
                    a_tag['href'] = '/media/{}/{}/{}/{}.{}'.\
                        format(link.group("year"), link.group("month"),\
                               link.group("day"),uri_to_iri(link.group("file")),\
                               link.group("ext"))
                    a_tag['data-gallery'] = ""
                    i = i.wrap(a_tag)
    return soup
