#!/usr/bin/env python

import logging,logging.config
import os
from subprocess import call
from datetime import datetime

import requests
import simplejson as json

import ia


logging.config.fileConfig('logging.conf')
cLogger = logging.getLogger('console')

def get_page(page_number):
    url = 'http://freemusicarchive.org/api/get/albums.json'
    params = dict(sort_by='album_date_released',sort_dir='desc',
                  page=page_number)
    dataset = ia.parse(url,params).json()
    return dataset

def get_tracks(album_id):
    url = 'http://freemusicarchive.org/api/get/tracks.json'
    params = dict(album_id=album_id,limit=50)
    tracks = ia.parse(url,params).json()['dataset']
    track_ids = [ x['track_id'] for x in tracks ]
    license = tracks[0]['license_url']
    artist_website = tracks[0]['artist_website']

    # Download every track for the given album.
    for track in track_ids:
        url = ('http://freemusicarchive.org/services/track/single/%s.json' % 
               track)
        track_dict = ia.parse(url).json()
        track_url = track_dict['track_file_url']
        track_name = track_dict['track_file'].split('/')[-1]
        wget = 'wget -nc "%s" -O "%s"' % (track_url, track_name)
        call(wget, shell=True)
        
    return license, artist_website
    
def main():
    total_pages = get_page(1)['total_pages']
    ia.make('FMA').dir()
    home = os.getcwd()
    for page_number in range(1,total_pages):
        dataset = get_page(page_number)['dataset']
        for item in dataset:
            identifier = '%s-%s' % (item['album_handle'],item['album_id'])

            # Make meta_dict if the item doesn't already exist on the Archive.
            if not ia.details(identifier).exists():
                ia.make(identifier).dir()
                date_parsed = datetime.strptime(item['album_date_released'], 
                                                '%m/%d/%Y').strftime('%Y-%m-%d')
                d = dict(title=item['album_title'], 
                         source=item['album_url'],
                         date=date_parsed,
                         creator=item['artist_name'],
                         artist_url=item['artist_url'],
                         producer=item['album_producer'],
                         album_type=item['album_type'],
                         engineer=item['album_engineer'],
                         description=item['album_information'],
                         mediatype='audio',
                         collection='freemusicarchive')

                tracks = get_tracks(item['album_id'])
                d['licencesurl'] = tracks[0]
                d['artist_website'] = tracks[1]

                # Delete dictionary items with empty values.
                meta_dict = dict([(k,v) for k,v in d.items() if v != None])
                
                ia.make(identifier, meta_dict).metadata()

                os.chdir(home)

            else:
                cLogger.info('%s is already in the Archive.' % identifier)

if __name__ == "__main__":
    main()
