# About

get-fma.py ingests content from http://freemusicarchive.org into 
http://archive.org on a daily basis. Most of the code is not specific to 
archive.org, and the script could easily be tweaked for general use.
(by ignoring fma.php, and doing a bit of clean-up to get-fma.py).


# Description

get-fma.py parses through JSON returned by the FMA API 
(http://freemusicarchive.org/api/docs/), generates the necessary metadata
files for archive.org ({item}_files.xml, {item}_meta.xml), and downloads
the audio for each item.

The files are prepared in a manner that is directly compatabile with
the Internet Archive's internal tool, auto_submit.php (one item per directory,
and all of the necessary metadata files). fma.php is the bridge between
auto_submit.php and get-fma.py. auto_submit.php automatically runs fma.php
once everyday. fma.php executes get-fma.py. When get-fma.py finishes executing,
fma.php hands off a list of items to auto_submit.php for ingestion.

At this point the ingest process can be monitored from the Internet Archive
catalog (http://www.archive.org/catalog.php?justme=1).


# Archive and Log files created by get-fma.py

+ {date}-fma.log:
  This log file is simply a dump of the stdout from get-fma.py.

+ ready_list.txt:
  this is the item list that auto_submit.php will use to ingest the content
 
+ ready_list.txt.lck:
  this file is created when get-fma.py starts running to prohibit 
  auto_submit.php from ingesting the item list before it is ready. When
  get-fma.py is finished running, ready_list.txt is deleted. 

* Various tasklogs are created by archive.org during the ingestion process.
These include the auto_submit.php tasklog, and the individual tasklogs for
each item (archive.php, derive.php, bup.php, etc.).


# TODO

+ Implement cleaner logging.
+ Prepare for FMA API changes ( "Starting in April 2012, we will refuse API 
  queries without a valid API key." ).
+ Start grabbing album images if available for item.
