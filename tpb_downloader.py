#!/usr/bin/python

import sys
import re
import json
import urllib2
import urllib
import subprocess
import argparse
import gzip

from HTMLParser import HTMLParser
from StringIO import StringIO

PIRATEBAY_URL = "thepiratebay.org"
# part of the piratebay URI to specific torrents
HDPATH = '0/7/208'
PATH = '0/7/200'

#TODO: move out class to a separate file
class MyHTMLParser(HTMLParser, object):

	def __init__(self, title, next_episode, preferred_magnet_link = None):
		"""
		redefining init to pass episode id and store preferred_magnet_link (ettv has highest priority)
		"""
		super(MyHTMLParser, self).__init__()
		self.title = title
		self.next_episode = next_episode
		self.preferred_magnet_link = preferred_magnet_link

	def handle_starttag(self, tag, attrs):
		"""
		redefining handle_starttag to parse out magnet link for the required episode and add it for download
		"""
		if tag == 'a':
			link = attrs[0][1]
			# finding all magnet links for this episode
			if re.search(("^magnet(.+?)%s" % self.next_episode), link):
				# updating preferred link if we find ettv or it's the first link that we find
				if "ettv" in link or self.preferred_magnet_link is None:
					self.preferred_magnet_link = link

	def close(self):
		"""
		downloading preferred_magnet_link
		"""
		if self.preferred_magnet_link is not None:
			print "Woooohoo, found NEW EPISODE %s!" % self.next_episode
			add_torrent(self.preferred_magnet_link)
			increment_episode_id(self.title, self.next_episode)
			# from HTMLParser.close() doc: redefined version should always call the HTMLParser base class method close()
			super(MyHTMLParser, self).close()

def check_if_transmission_is_running():
	try:
		subprocess.check_output(["transmission-remote", "-l"], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as err:
		if "Couldn't connect to server" in err.output:
			print "The server is stopped, starting..."
			subprocess.call(["transmission-daemon"])
			print "The server is started."
		else:
			print "Unrecognized error: %s" % err.output

def add_torrent(magnet_link):
	try:
		subprocess.check_output(["transmission-remote", "-a", magnet_link], stderr=subprocess.STDOUT)
		print "New episode was scheduled for downloading"
	except subprocess.CalledProcessError, err:
		print "Could not schedule torrent: %s, the command was %s" % (err.output, err.cmd), 'error'
		raise

def increment_episode_id(title, next_episode):
	# TODO: change config structure to search by key instead of iterating over all of the objects
	for series in data:
		if series['title'] == title:
			if series['next_episode'] == series['final_episode']:
				series['active'] = 'no'
				print "Alas, this was the last episode in this series :("
			current_split = next_episode.split('E')
			# incrementing episode number
			next = current_split[0] + 'E' + str(int(current_split[1]) + 1).zfill(2)
			print "Next episode will be", next
			series['next_episode'] = next

def main():

	# TODO: get rid of globals
	global data

	parser = argparse.ArgumentParser()
	#nargs + const=False make is possible to just specifiy '-nohd' without params to pass False value, if -nohd is not passed the default value is taken
	parser.add_argument('-nohd', nargs='?', default=True, const=False, type=bool, dest='isHD', help='defines whether low quality episodes should be downloaded')
	parser.add_argument('-c', '--config', default='config.json', dest='config', help='config with series to be checked')
	
	options = parser.parse_args()

	if options.isHD:
		video_quality_path = HDPATH
	else:
		video_quality_path = PATH

	check_if_transmission_is_running()
	
	jsonfile = open(options.config, "r")
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
				# TODO: add 2-3 retries since TPB often returns 502: Bad Gateway which is reaaaaally annoying
				response = urllib2.urlopen(search_request)
			except urllib2.URLError as err:
				print "\nERROR:\n%s\nLooks like TPD is down again :(" %str(err.reason), 'error'
				print "The query was: %s\n" % url, 'error'
				raise
			except KeyboardInterrupt:
				print "\nOkok, you're the boss, exiting..."
				sys.exit(0)
			except:
				print "Unexpected error:"
				raise

			# handling cases when pages are gzipped
			if response.info().get('Content-Encoding') == 'gzip':
				print "gzipped!"
				buf = StringIO(response.read())
				f = gzip.GzipFile(fileobj=buf)
				content_parseme = f.read()
			else:
				content_parseme = response.read()

			page_parser = MyHTMLParser(series['title'], series['next_episode'])
			page_parser.feed(content_parseme)
			page_parser.close()

			print 'Previous episodes can be downloaded here: %s' % url
	
	# let's see if we can still serialize it...
	try:
		serialized = json.dumps(data, indent=4)
	except TypeError as err: 
		print "ERROR: Config object is corrupted, exiting without writing to %s" % options.config
		raise

	# writing updated config to the FS
	jsonfile = open(options.config, "w")
	jsonfile.write(serialized)
	jsonfile.close()
	
if __name__ == "__main__":
	main()