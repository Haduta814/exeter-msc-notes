import ast
import xml.etree.ElementTree as ET
import json
from collections import defaultdict
import gzip
from tqdm import tqdm
import bz2

fileroot = 'simplewiki-20250801'

pageid_to_linkid = defaultdict(list)
with gzip.open(fileroot+"-pagelinks.sql.gz", "rt") as f:
	for line in tqdm(f, total=488, desc="Reading pagelinks"):
		if line[:6] =='INSERT':# INTO `pagelinks` VALUES':
			values = line.split()[4].rstrip(';')
			data_list = ast.literal_eval(f"[{values}]")
			for d in data_list:
				if d[1] == 0:
					pageid_to_linkid[ d[0] ].append( d[2] )
					
with open('pageid_to_linkid.json', 'w') as outfile: json.dump(pageid_to_linkid, outfile, ensure_ascii=False)
print("Wrote pageid_to_linkid");

linkid_to_title = {}
with gzip.open(fileroot+"-linktarget.sql.gz", "rt") as f:
	for line in tqdm(f, total=142, desc="Reading linktarget"):
		if line[:6] =='INSERT': # INTO `linktarget` VALUES':
			values = line.split()[4].rstrip(';')
			data_list = ast.literal_eval(f"[{values}]")
			for d in data_list:
				if d[1] == 0:
					linkid_to_title[d[0]] = d[2]
with open('linkid_to_title.json', 'w') as outfile: json.dump(linkid_to_title,outfile, ensure_ascii=False )
print("Wrote linkid_to_title");


pageid_to_title = {}
title_to_pageid = {}
title_to_canonicaltitle = {}
ns = {"mw": "http://www.mediawiki.org/xml/export-0.11/"}
with bz2.open(fileroot + "-pages-articles.xml.bz2", "rt") as f:
	for event, elem in tqdm( ET.iterparse(f, events=("end",)), total=8915454, desc="Reading articles"):
		if elem.tag == f"{{{ns['mw']}}}page": 
			wikins = int(elem.findtext("mw:ns", namespaces=ns))
			if wikins != 0 : continue
			title = elem.findtext("mw:title", namespaces=ns)
			page_id = int( elem.findtext("mw:id", namespaces=ns) )
			redirect_elem = elem.find("mw:redirect", namespaces=ns)
			redirect_title = redirect_elem.attrib["title"] if redirect_elem is not None else None
			if redirect_title:
				title_to_canonicaltitle[title] = redirect_title

			pageid_to_title[page_id] = title
			title_to_pageid[title] = page_id

			elem.clear()

with open('pageid_to_title.json', 'w') as outfile: json.dump(pageid_to_title,outfile, ensure_ascii=False )
with open('title_to_pageid.json', 'w') as outfile: json.dump(title_to_pageid,outfile, ensure_ascii=False )
with open('title_to_canonicaltitle.json', 'w') as outfile: json.dump(title_to_canonicaltitle,outfile, ensure_ascii=False )

print("Parsed article titles");


with open('pageid_to_linkid.json', 'r') as infile: pageid_to_linkid = json.load(infile)
with open('linkid_to_title.json', 'r') as infile: linkid_to_title = json.load(infile)
with open('pageid_to_title.json', 'r') as infile: pageid_to_title = json.load(infile)
with open('title_to_pageid.json', 'r') as infile: title_to_pageid = json.load(infile)
with open('title_to_canonicaltitle.json', 'r') as infile: title_to_canonicaltitle = json.load(infile)

pageid_to_pageid = defaultdict(list)
for pageid, links in pageid_to_linkid.items():
	pageid = str(pageid)
	pagetitle = pageid_to_title[pageid]
	
	redirect = False
	if pagetitle in title_to_canonicaltitle: #links on redirect page are counted with the canonical page links
		continue	#not looking for links on redirect pages
		
	

	for linkid in links:
		linkid = str(linkid)
		if linkid not in linkid_to_title: continue  #not in namespace 0
		
		linktitle = linkid_to_title[ str(linkid) ].replace('_', ' ')
		
		if linktitle in title_to_pageid:

			if linktitle in title_to_canonicaltitle:
				linktitle = title_to_canonicaltitle[ linktitle ]
				if linktitle == pagetitle: continue
				
			if linktitle in title_to_pageid: #otherwise link to a ns !=0 page so skip it
				pageid_to_pageid[ pageid ].append( int( title_to_pageid[linktitle] ) )


#remove repeats			
for pageid in pageid_to_pageid: pageid_to_pageid[pageid] = list(set(pageid_to_pageid[pageid]))

with open('pageid_to_pageid.json', 'w') as outfile: json.dump( dict(pageid_to_pageid), outfile, ensure_ascii=False, indent=2 )
print("Built page to page network");

