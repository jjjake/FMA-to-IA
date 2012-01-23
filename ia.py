#!/usr/bin/env python

import os
import requests
import simplejson
from urllib import urlencode
from lxml import etree


class details:


    def __init__(self, item):
        self.item = item
        self.request = requests.get('http://archive.org/metadata/%s' % 
                                    self.item)
        self.headers = self.request.headers
        self.json_str = simplejson.loads(self.request.content)

    def files(self):
        return self.json_str['files']
    def metadata(self):
        return self.json_str['metadata']
    def reviews(self):
        return self.json_str['reviews']
    def server(self):
        return self.json_str['server']
    def dir(self):
        return self.json_str['dir']

    def exists(self):
        if self.json_str == {}:
            return 0
        if self.json_str != {}:
            return 1


class search:

    def __init__(self, query):
        self.query = urlencode(query)
        self.search_url = ('http://www.archive.org/advancedsearch.php?%s' % 
                           self.query)
        self.request = requests.get(self.search_url)
        self.headers = self.request.headers
        self.json_str = simplejson.loads(self.request.content)

    def response(self):
        return self.json_str['response']
    def responseHeader(self):
        return self.json_str['responseHeader']


class upload:

    def __init__(self, item, file):
        self.s3_endpoint = 'http:s3.us.archive.org/%s/%s' % (item, file)

    def uploadz(self):
        h = {'x-amz-auto-make-bucket': '1', 
             'x-archive-meta01-collection': 'test_collection',
             'x-archive-meta-mediatype': 'texts',
             'authorization': 'LOW U7TwGpIjERYE9cx4:47gEsUpL4y4tR4iE'}
        d = open('intro_to_auto_submit.pdf','rb')
        r = requests.put(self.s3_endpoint, data=h)
        return r.status_code

class parse:

    def __init__(self, url, params=None):
        self.request = requests.get(url=url, params=params)
        self.json_str = simplejson.loads(self.request.content)

    def json(self):
        return self.json_str


class make:
    
    def __init__(self, identifier, meta_dict=None):
        self.identifier = identifier
        self.meta_dict = meta_dict

    def metadata(self):
        f = open("%s_files.xml" % self.identifier, "wb")
        f.write("<files />")
        f.close()
        root = etree.Element("metadata")
        for k,v in self.meta_dict.iteritems():
            subElement = etree.SubElement(root,k)
            subElement.text = v
        metaXml = etree.tostring(root, pretty_print=True,
                                 xml_declaration=True, encoding="utf-8")
        ff = open("%s_meta.xml" % self.identifier, "wb")
        ff.write(metaXml)
        ff.close()

    def dir(self):
        if not os.path.exists(self.identifier):
            os.mkdir(self.identifier)
        os.chdir(self.identifier)
