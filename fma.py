#!/usr/bin/env python
import logging,logging.config
import os
from datetime import datetime

import requests
from lxml import etree
import lxml.html


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
logging.config.fileConfig('logging.conf')
c_logger = logging.getLogger('console')

DATA_DIR = '/1/incoming/tmp/FMA'
SKIP = [x.strip() for x in 'itemlist.txt']


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def download(url, filename):
    r = requests.get(url)
    if r.status_code != 200:
        return False
    with open(filename, 'wb') as f:
        f.write(r.content)
    return True

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_page(page_number):
    url = 'http://freemusicarchive.org/api/get/albums.json'
    params = dict(
            sort_by='album_date_released', 
            sort_dir='desc',
            limit=50, 
            page=page_number, 
            api_key='YRSCRTKY',
    )
    r = requests.get(url, params=params)
    return r.json()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_tracks(album_id):
    u = 'http://freemusicarchive.org/api/get/tracks.json'
    params = dict(album_id=album_id, limit=50, api_key='WS35J1MULKPQQOEI')
    r = requests.get(u, params=params)
    tracks = r.json()['dataset']
    track_ids = [ x['track_id'] for x in tracks ]
    try:
        license = tracks[0]['license_url']
        artist_website = tracks[0]['artist_website']
    except IndexError:
        license = None
        artist_website = None
        logging.warning('No license! album ID: %s' % album_id)

    # Download every track for the given album.
    for track in track_ids:
        u = ('http://freemusicarchive.org/services/track/single/%s.json' %
             track)
        r = requests.get(u)
        track_dict = r.json()
        track_url = track_dict['track_file_url']
        track_name = track_dict['track_file'].split('/')[-1]
        c_logger.info('Downloading track: %s' % track_name)

        download(track_url, track_name)
    return license, artist_website

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def download_album_image(metadata):
    r = requests.get(metadata['source'])
    html = lxml.html.fromstring(r.content)
    img_src = html.xpath("//div[@class='album-image']//img")[0].attrib['src']
    img_url = img_src.replace('?width=290&height=290','')
    filename = '{0}.jpg'.format(metadata['identifier'])
    download(img_url, filename)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def write_item_xml(metadata, root=etree.Element('metadata')):
    with open("%s_files.xml" % metadata['identifier'], 'w') as f:
        f.write("<files />")
    for k,v in metadata.iteritems():
        subElement = etree.SubElement(root,k)
        subElement.text = v
    meta_xml = etree.tostring(root, 
                              pretty_print=True, 
                              xml_declaration=True, 
                              encoding="utf-8")
    with open("%s_meta.xml" % metadata['identifier'], 'w') as f:
        f.write(meta_xml)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def process_dataset(dataset):
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    os.chdir(DATA_DIR)
    for item in dataset:
        identifier = '{0}-{1}'.format(item['album_handle'][:70],
                                      item['album_id']).strip('-_')
        if identifier in SKIP:
            continue

        c_logger.info('Creating item: https://archive.org/details/{0}'.format(identifier))
        if not os.path.exists(identifier):
            os.mkdir(identifier)
        os.chdir(identifier)

        md = dict(
                identifier=identifier,
                collection='freemusicarchive',
                mediatype='audio',
                title=item['album_title'],
                source=item['album_url'],
                creator=item['artist_name'],
                artist_url=item['artist_url'],
                producer=item['album_producer'],
                album_type=item['album_type'],
                engineer=item['album_engineer'],
                description=item['album_information'],
                TEST=None,
        )
        try:
            md['date'] = datetime.strptime(item['album_date_released'],
                                           '%m/%d/%Y').strftime('%Y-%m-%d')
        except TypeError:
            c_logger.warning('This album has no date!')

        """Download every track on album. Also return licenseurl, artist_website
        (the license URL and artist's website is only available in the 'track'
        dataset).
        """
        tracks = get_tracks(item['album_id'])
        md['licenseurl'] = tracks[0]
        md['artist_website'] = tracks[1]

        metadata = dict((k,v) for k,v in md.items() if v)

        try:
            download_album_image(metadata)
        except IndexError:
            c_logger.warning('This album does not have an image')
        write_item_xml(metadata)
        os.chdir(DATA_DIR)
    c_logger.info('YOU HAVE SO MUCH MUSIC!')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == "__main__":
    total_pages = get_page(1)['total_pages']
    for page_number in range(0, total_pages):
        print '\nPage: {0}/{1}\n'.format(page_number,total_pages)
        dataset = get_page(page_number)['dataset']
        process_dataset(dataset)
