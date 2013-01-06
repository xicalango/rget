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
	STAT_IDLE = 0
	STAT_DL = 1
	STAT_FIN_GOOD = 2
	STAT_FIN_BAD = 3
	STAT_FIN_USER = 4

	def __init__(self, url, outputDir = '.'):
		Thread.__init__(self, name='WGet ' + url)
		self.url = url
		self.outputDir = outputDir
		self.info = WGetInfo()
		self.running = False
		self.status = WGetProcess.STAT_IDLE
		self.exit_status = None

	def run(self):
		self.running = True
		self.proc = subprocess.Popen(['wget', '--progress=dot', '-P', self.outputDir, self.url], stderr=subprocess.PIPE)

		self.status = WGetProcess.STAT_DL

		while self.proc.poll() == None and self.running:
			line = self.proc.stderr.readline()
			self.info.update(line)

		if self.running == False:
			self.status = STAT_FIN_USER
			self.proc.kill()
		else:
			self.running = False
			if self.proc.returncode == 0:
				self.status = STAT_FIN_GOOD
			else:
				self.status = STAT_FIN_BAD


