# About

**FMA to IA** can be used to ingest content from http://freemusicarchive.org
into http://archive.org. Most of the code is not specific to archive.org, 
and the script could easily be tweaked for general use.


# Description

`fma.py` parses through JSON returned by the FMA API 
(http://freemusicarchive.org/api/docs/), generates the necessary metadata
files for archive.org ({item}_files.xml, {item}_meta.xml), and downloads
the audio for each item.

The files are prepared in a manner that is directly compatabile with
the Internet Archive's internal tool, `auto_submit.php`. `fma.php` is the 
bridge between `auto_submit.php` and `fma.py`. `auto_submit.php` is scheduled
to run `fma.php` once everyday. In turn, `fma.php` executes `fma.py`. When 
`fma.py` finishes executing, `fma.php` hands off a list of items to 
`auto_submit.php` for ingestion into http://archive.org.  At this point the 
ingest process can be monitored from the Internet Archive catalog 
(http://www.archive.org/catalog.php?justme=1).


# Archive and Log files created by get-fma.py

+ `{date}-fma.log`:
  This log file is simply a dump of the stdout from get-fma.py.

+ `ready_list.txt`:
  this is the item list that `auto_submit.php` will use to ingest the content
 
+ `ready_list.txt.lck`:
  this file is created when `fma.py` starts running to prohibit 
  `auto_submit.php` from ingesting the item list before it is ready. When
  `fma.py` is finished running, `ready_list.txt` is deleted. 

