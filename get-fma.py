#!/1/data/ENV/bin/python

from lxml import etree
import urllib2
from urllib2 import HTTPError
import os
import string
from datetime import datetime
import time
from subprocess import call
import sys

import chardet

def getXml(pageUrl, data):
    doc = etree.parse(urllib2.urlopen(pageUrl)).getroot()
    dataset = doc.find('dataset')
    if data == 1:
        return doc
    if data == 2:
        return dataset

def getTracks(albumID, data):
    ### Return a list of download Urls for given albumID
    trackUrl = ( 'http://freemusicarchive.org/api/get/tracks.xml?album_id=%s' %
                 albumID )
    trackXml = getXml(trackUrl, 2)
    trackList = []
    for value in trackXml:
        trackDict = dict(((elt.tag,elt.text) for elt in value))
        trackID = trackDict['track_id']
        trackUrl = ( 'http://freemusicarchive.org/services/track/single/%s.xml' %
                     trackID )
        track = getXml(trackUrl, 1)
        for downloadUrl in track:
            song = dict(((elt.tag,elt.text) for elt in track))
            songD = song['download']
        trackList.append(songD)
    if data == 1:
        return trackXml
    if data == 2:
        return trackList

def sanitizeString(dirty):
    clean = string.replace(dirty,"'",'')
    clean = string.replace(dirty," ",'')
    clean = string.replace(clean,'"','')
    clean = string.replace(clean,';','')
    clean = string.replace(clean,'.','')
    clean = string.replace(clean,'&','')
    clean = string.replace(clean,',','')
    clean = string.replace(clean,'!','')
    clean = string.replace(clean,'[','')
    clean = string.replace(clean,']','')
    return clean

def makeUTF8(string):
    try:
        enc = chardet.detect(str(string))['encoding']
        string = u'%s' % string.decode(enc,'replace').encode('utf-8','replace')
    except UnicodeEncodeError:
        string = None
    return string

def download(urlList, trackDict):
    retries = 0
    for song in urlList:
        req = urllib2.Request(song)
	for i in range(0,10):
	    while True:
                try:
                    response = urllib2.urlopen(song)
                except HTTPError, e:
                    print ( "Error Code: %s, Let's wait a second and retry..." %
                            e.code )
		    time.sleep(10)
		    continue
		break
        data = response.read()
        try:
            localName = ( (response.headers['Content-Disposition']).split(
                          'filename=')[1] )
        except KeyError:
            localName = trackDict['track_title'].replace(' ', '_')    
        localName = localName.replace('/', '-')
        localName = localName.encode('utf-8')
        print 'downloading %s from: %s' % (localName, song)
        f = open(localName, 'wb')
        f.write(data)
        f.close()

def main():
    ### Perpetual Loop Auto-submit business:
    home = os.getcwd()
    readyListFileName = "ready_list.txt"
    f = open(readyListFileName,'wb')
    f.write()
    lockFileName = readyListFileName + ".lck"
    ### Exit if last list still pending, wait for it to be renamed/removed.
    if os.access( readyListFileName, os.F_OK ) is True:
        print ( 'ABORT: %s exists (Not picked up yet? Should be renamed'
                'when retrieved by auto_submit loop!)' % readyListFileName ) 
        if os.access( lockFileName, os.F_OK ) is True:
            os.remove(lockFileName)
        exit(0)
    ### If lock file exists, another process is already generating the list
    if os.access( lockFileName, os.F_OK ) is True:
        print ( 'ABORT: %s lockfile exists (Another process generating list'
                'already? Should be deleted when complete!)' % lockFileName )
        exit(0)
    ### Touch a lock file while the script is running.
    open( lockFileName, 'w' ).close()

    if not os.path.exists('/1/incoming/tmp/FMA'):
        os.mkdir('/1/incoming/tmp/FMA')
    os.chdir('/1/incoming/tmp/FMA')
    dataHome = os.getcwd()
    for i in range(0, 400):
        url = ( 'http://freemusicarchive.org/api/get/albums.xml?'
                'sort_by=album_id&sort_dir=desc&page=%s' % i )
        print "\n*** Page: %s ***\n\n" % i
        dataset = getXml(url, 2)
        ### For every album in given dataset:
        for value in dataset:
            albumDict = dict(((elt.tag,elt.text) for elt in value))
            albumHandle = albumDict['album_handle'].replace(' ','')
            archiveID = "%s-%s" % (albumHandle, albumDict['album_id'])
            archiveID = sanitizeString(archiveID.lstrip(' -_'))
            archiveID = makeUTF8(archiveID)
            if len(archiveID) <= 4:
                archiveID = ( "%s-%s-%s" % (albumDict['artist_name'], 
                              albumHandle, albumDict['album_id']) )
                archiveID = sanitizeString(archiveID)
                archiveID = makeUTF8(archiveID)
            elif len(archiveID) >= 70:
                archiveID = ( "%s-%s" % (albumDict['artist_name'], 
                              albumDict['album_id']) )
                archiveID = sanitizeString(archiveID)
                archiveID = makeUTF8(archiveID)
            ### Check to see if this item is already in the Archive.
            check_item = ( '/usr/bin/curl -s --location "http://www.archive.org'
                           '/services/check_identifier.php?identifier=%s"'
                           '| if grep -q "not_available"; then return 1; fi' %
                           archiveID )
            check_item = str(check_item)
            retcode = call(check_item, shell=True)
            if retcode != 0:
                print ( "\n---%s seems to already be in the archive..."
                        "Let's try the next item\n\n" % archiveID )
            else:
                print "\n---Creating item: %s---\n\n" % archiveID
                if not os.path.exists(archiveID):
                    os.mkdir(archiveID)
                os.chdir(archiveID)
                ### Create {item}_meta.xml for each album
                print 'Generating %s_meta.xml for %s\n' % (archiveID, archiveID)
                if albumDict['album_date_released'] != None:
                    archiveDate = ( datetime.strptime(
                                    albumDict['album_date_released'], 
                                    '%m/%d/%Y').strftime('%Y-%m-%d') )
                if albumDict['album_date_released'] == None:
                    try:
                        archiveDate = ( datetime.strptime(
                                        albumDict['album_date_created'], 
                                        '%m/%d/%Y %I:%M:%S %p').strftime(
                                        '%Y-%m-%d') )
                    except ValueError:
                        archiveDate = None
                metaDict = dict(source=albumDict['album_url'],
                                title=albumDict['album_title'],
                                creator=albumDict['artist_name'],
                                artistUrl=albumDict['artist_url'],
                                date=archiveDate,
                                producer=albumDict['album_producer'],
                                engineer=albumDict['album_engineer'],
                                description=albumDict['album_information'])
                for x in list(metaDict.keys()):
                    if metaDict[x] == None:
                        del metaDict[x]
                root = etree.Element("metadata")
                for k,v in metaDict.iteritems():
                    subElement = etree.SubElement(root, k)
                    subElement.text = v
                trackXml = getTracks(albumDict['album_id'], 1)
                for value in trackXml:
                    trackDict = dict(((elt.tag,elt.text) for elt in value))
                for x in list(trackDict.keys()):
                    if trackDict[x] == None:
                        del trackDict[x]
                try:
                    artist_website = etree.SubElement(root, 'artist_website')
                    artist_website.text = trackDict['artist_website']
                    license = etree.SubElement(root, 'licenseurl')
                    license.text = trackDict['license_url']
                except KeyError:
                    pass
                mediatype = etree.SubElement(root, 'mediatype')
                mediatype.text = 'audio'
                creator = etree.SubElement(root, 'creator')
                creator.text = trackDict['artist_name']
                collection = etree.SubElement(root, 'collection')
                collection.text = 'freemusicarchive'
                metaXml = etree.tostring(root, pretty_print=True, 
                                         xml_declaration=True, encoding="utf-8")
                f = open("%s_meta.xml" % archiveID, 'wb')
                f.write(metaXml)
                f.close()
                ff = open("%s_files.xml" % archiveID, 'wb')
                ff.write('<files/>')
                ff.close()
                ### Download all of the tracks for the album
                trackList = getTracks(albumDict['album_id'], 2)
                download(trackList, trackDict)
                time.sleep(3)
            os.chdir(dataHome)

    os.chdir(home)
    dataList = os.listdir(dataHome)
    f = open(readyListFileName,'wb')
    f.write('\n'.join(dataList))
    ### Remove lock file...
    os.remove(lockFileName)
    print '\n!!!\nYOU HAVE SO MUCH MUSIC\n'

if __name__ == "__main__":
    sys.exit(main())

