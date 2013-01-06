#!/usr/bin/env python

import subprocess
import re
from threading import Thread

class WGetInfo(object):
	STATUS_REGEX = re.compile("[ \t]*(?P<data>[0-9]+)(?P<data_unit>[ KMG])[ '.']*(?P<percent>[0-9]+)%[ ]*(?P<speed>[0-9]+)(?P<speed_unit>[ KMG])[ =](?P<time>[0-9dhms ]+)")
 

	def __init__(self):
		self.completeData = 0
		self.data = 0
		self.data_unit = ' '
		self.process = 0
		self.speed = 0
		self.speed_unit = ' '
		self.time = ''
	
	def update(self, line):
		
		r = WGetInfo.STATUS_REGEX.search(line)
		if r != None:
			self.status_update(r.groupdict())

	def status_update(self, status):
		self.data = status['data']
		self.data_unit = status['data_unit']
		self.process = status['percent']
		self.speed = status['speed']
		self.speed_unit = status['speed_unit']
		self.time = status['time']
	
	def __str__(self):
		return str(self.data) + self.data_unit + " (" + str(self.process) + "%)"

class WGetProcess(Thread):
	def __init__(self, url, outputDir = '.'):
		Thread.__init__(self, name='WGet ' + url)
		self.url = url
		self.outputDir = outputDir
		self.info = WGetInfo()
		self.running = False

	def run(self):
		self.running = True
		self.proc = subprocess.Popen(['wget', '--progress=dot', '-P', self.outputDir, self.url], stderr=subprocess.PIPE)
		while self.proc.poll() == None and self.running:
			line = self.proc.stderr.readline()
			self.info.update(line)
			print self.info

		if self.running == False:
			self.proc.kill()

		self.running = False


wget = WGetProcess('http://cdimage.debian.org/debian-cd/6.0.6/i386/iso-cd/debian-6.0.6-i386-businesscard.iso')

wget.start()
