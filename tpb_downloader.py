#!/usr/bin/python

import sys
import json
import urllib2
import urllib
import logging
import subprocess
import argparse
import gzip

from HTMLParser import HTMLParser
from StringIO import StringIO

PIRATEBAY_URL = "thepiratebay.org"
# part of the piratebay URI to specific torrents
HDPATH = '0/7/208'
PATH = '0/7/200'

class MyHTMLParser(HTMLParser):

	def __init__(self, title, next_episode, already_downloaded = False):
		# need to pass the episode id when initializing the object so creating a custom class
		HTMLParser.__init__(self)
		self.title = title
		self.next_episode = next_episode
		self.already_downloaded = already_downloaded

	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			# it's a list of tuples, we need to get the second value of the first tuple
			listeg = attrs[0]

			# getting magnet link for needed episode if it's already out:
			# do it via mask? need to add 'HD' and 'eztv'
			if "magnet" in listeg[1] and self.next_episode in listeg[1] and self.already_downloaded == False:
				print "Woooohoo, found NEW EPISODE %s!" % self.next_episode
				try:
					output = subprocess.check_output(["transmission-remote", "-a", listeg[1]], stderr=subprocess.STDOUT)
					print "New episode is scheduled for downloading"
				except subprocess.CalledProcessError, err:
					print "Could not schedule torrent: %s, the command was %s" % (err.output, err.cmd), 'error'
				# we've downloaded the torrent, no need to check the rest, maybe we need to call destruct to save the time?
				else:
					for series in data:
						if series['title'] == self.title:
							if series['next_episode'] == series['final_episode']:
								series['active'] = 'no'
								print "Alas, this was the last episode in this series :("
							current_split = self.next_episode.split('E')
							#incrementing episode number
							next = current_split[0] + 'E' + str(int(current_split[1]) + 1).zfill(2)
							print "Next episode will be", next
							series['next_episode'] = next
				#should be set only if there was no exception -> in 'else'
				self.already_downloaded = True

def check_if_client_running():
	try:
		subprocess.check_output(["transmission-remote", "-l"], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError, err:
		print err.output
		print "The server is stopped, starting..."
		subprocess.call(["transmission-daemon"])
		print "The server is started."

def main():

	global data

	parser = argparse.ArgumentParser()
	parser.add_argument('-hd', nargs='?', default=True, const=True, type=bool, dest='isHd', help='defines whether HD quality episodes should be downloaded')
	parser.add_argument('-c', '--config', default='config.json', dest='config', help='config with series to be checked')
	
	options = parser.parse_args()

	if options.isHd:
		video_quality_path = HDPATH
	else:
		video_quality_path = PATH
	
	#reading config and closing it
	jsonfile = open(options.config)
	data = json.load(jsonfile)
	jsonfile.close()

	for series in data:
	# checking updates for active series only
		if series['isActive'] == True:
			
			print "\n ====%s==== " % (series['title'])
			print "Searching for episode %s..." % series['next_episode']

			# escaping spaces and special characters
			url_part = urllib.quote(series['title'])
			url = "https://" + PIRATEBAY_URL + "/search/%s/%s" % (url_part, video_quality_path)
			# spoofing user agent header to fool TPB bot protection
			search_request = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})

			try:
				response = urllib2.urlopen(search_request)
			except KeyboardInterrupt:
				print "\nOkok, you're the boss, exiting..."
				sys.exit(0)
			except urllib2.URLError as err:
				print "\nERROR:\n%s\nLooks like TPD is down again :(" %str(err.reason), 'error'
				print "The query was: %s\n" % url, 'error'
				sys.exit(1)
			except:
				print "Unexpected error:"
				raise

			# handling cases when pages are gzipped
			if response.info().get('Content-Encoding') == 'gzip':
				print "gzipped!"
				buf = StringIO( response.read())
				f = gzip.GzipFile(fileobj=buf)
				content_parseme = f.read()
			else:
				content_parseme = response.read()

			parser = MyHTMLParser(series['title'], series['next_episode'])
			parser.feed(content_parseme)
			print 'Previous episodes can be downloaded here: %s' % url

	#writing resulting config:
	jsonfile = open(options.config, "w+")
	jsonfile.write(json.dumps(data, indent=4))
	jsonfile.close()

if __name__ == "__main__":
	main()