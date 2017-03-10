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


"""def sidebarThumbnail(file_link, post_id):
    ext = file_link.split('.')[-1].lower()
    link = findLink(iri_to_uri(file_link))
    file = uri_to_iri(findFile(link))
    if ext == "gif":
        file_out = uri_to_iri("/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}-thumb.webm"\
                    .format(link.group("year"), link.group("month"),
                        link.group("day"), link.group("file"), str(post_id)))
        file_out_gif = uri_to_iri("/tmp/{}-{}-thumb.gif"\
                    .format(link.group("file"), str(post_id)))
        link_out = uri_to_iri('/media/{}/{}/{}/{}-{}-thumb.webm'\
                .format(link.group("year"), link.group("month"),
                link.group("day"), link.group("file"), str(post_id)))
        resize_gif(file, save_as=file_out_gif, resize_to=(150,150))
        clip = VideoFileClip(file_out_gif)
        video = CompositeVideoClip([clip])
        video.write_videofile(file_out, codec='libvpx', fps=10,
                                            audio=False, preset='superslow')
        os.remove(file_out_gif)
        return link_out
    else:
        return saveImage(link, file, 150, h=150)"""



def saveImage(link, file, w, h=3500):

    file_out = '/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.{}'\
                        .format(link.group("year"), link.group("month"),
                        link.group("day"), uri_to_iri(link.group("file")),
                        w, link.group("ext"))

    link_out = '/media/{}/{}/{}/{}-{}.{}'\
            .format(link.group("year"), link.group("month"),
            link.group("day"), link.group("file"),
            w, link.group("ext"))
    img = Image.open(file)
    sz_tuple = (w, h)

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
            original_pic = uri_to_iri('/media/{}/{}/{}/{}.{}'.\
                    format(link.group("year"), link.group("month"),
                    link.group("day"), link.group("file"),
                    link.group("ext")))

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

                else:  # конвертим гифки в webm
                    file_out = uri_to_iri("/root/myblog/myblog/blog/static/media/{}/{}/{}/{}-{}.webm"\
                    .format(link.group("year"), link.group("month"),
                        link.group("day"), link.group("file"), str(post_id)))
                    link_out = uri_to_iri('/media/{}/{}/{}/{}-{}.webm'\
                            .format(link.group("year"), link.group("month"),
                            link.group("day"), link.group("file"), str(post_id)))

                    clip = VideoFileClip(file)
                    video = CompositeVideoClip([clip])
                    video.write_videofile(file_out, codec='libvpx',
                                            audio=False, preset='superslow')
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


def resize_gif(path, save_as=None, resize_to=None):
    """
    Resizes the GIF to a given length:

    Args:
        path: the path to the GIF file
        save_as (optional): Path of the resized gif. If not set, the original gif will be overwritten.
        resize_to (optional): new size of the gif. Format: (int, int). If not set, the original GIF will be resized to
                              half of its size.
    """
    all_frames = extract_and_resize_frames(path, resize_to)

    if not save_as:
        save_as = path

    if len(all_frames) == 1:
        print("Warning: only 1 frame found")
        all_frames[0].save(save_as, optimize=True)
    else:
        all_frames[0].save(save_as, optimize=True, save_all=True, append_images=all_frames[1:], loop=1000)


def analyseImage(path):
    """
    Pre-process pass over the image to determine the mode (full or additive).
    Necessary as assessing single frames isn't reliable. Need to know the mode
    before processing all frames.
    """
    im = Image.open(path)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results


def extract_and_resize_frames(path, resize_to=None):
    """
    Iterate the GIF, extracting each frame and resizing them

    Returns:
        An array of all frames
    """
    mode = analyseImage(path)['mode']

    im = Image.open(path)

    if not resize_to:
        resize_to = (im.size[0] // 2, im.size[1] // 2)

    i = 0
    p = im.getpalette()
    last_frame = im.convert('RGBA')

    all_frames = []

    try:
        while True:
            # print("saving %s (%s) frame %d, %s %s" % (path, mode, i, im.size, im.tile))

            '''
            If the GIF uses local colour tables, each frame will have its own palette.
            If not, we need to apply the global palette to the new frame.
            '''
            if not im.getpalette():
                im.putpalette(p)

            new_frame = Image.new('RGBA', im.size)

            '''
            Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
            If so, we need to construct the new frame by pasting it on top of the preceding frames.
            '''
            if mode == 'partial':
                new_frame.paste(last_frame)

            new_frame.paste(im, (0, 0), im.convert('RGBA'))

            new_frame.thumbnail(resize_to, Image.ANTIALIAS)
            all_frames.append(new_frame)

            i += 1
            last_frame = new_frame
            im.seek(im.tell() + 1)
    except EOFError:
        pass

    return all_frames

def stripMediaFromPath(file):
    """
    Strip "media/" from file's path
    """
    path = file.split(os.sep)[2:]
    new_path=""
    for i in path:
        new_path = os.path.join(new_path, i)
    return uri_to_iri(new_path)
