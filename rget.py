#!/usr/bin/env python

import subprocess
import re
from threading import Thread
from cmd import Cmd

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

	def __init__(self, url, outputDir = None):
		Thread.__init__(self, name='WGet ' + url)
		self.url = url
		self.outputDir = outputDir
		self.info = WGetInfo()
		self.running = False
		self.status = WGetProcess.STAT_IDLE
		self.exit_status = None

	def getParams(self):
		params = ['wget', '--progress=dot']

		if self.outputDir != None:
			params.append('-P')
			params.append(self.outputDir)

		params.append(self.url)

		return params

	def run(self):
		self.running = True

		params = self.getParams()

		self.proc = subprocess.Popen(params, stderr=subprocess.PIPE)

		self.status = WGetProcess.STAT_DL

		while self.proc.poll() == None and self.running:
			line = self.proc.stderr.readline()
			self.info.update(line)

		if self.running == False:
			self.status = WGetProcess.STAT_FIN_USER
			self.proc.kill()
		else:
			self.running = False
			if self.proc.returncode == 0:
				self.status = WGetProcess.STAT_FIN_GOOD
			else:
				self.status = WGetProcess.STAT_FIN_BAD


class Manager(object):
	def __init__(self):
		self.processes = []

	def add(self, url, outputDir = None):
		new_process = WGetProcess( url, outputDir = outputDir )
		self.processes.append( new_process )
		return new_process

	def addAndStart(self, url, outputDir = None):
		process = self.add(url, outputDir)
		process.start()
	
	def printAllInfo(self):
		for p in self.processes:
			print p.url
			print p.status
			print p.info
	
	def shutdown(self):
		for p in self.processes:
			p.running = False
			p.join()


class RGetConsole(Cmd):
	def __init__(self, manager):
		Cmd.__init__(self)
		self.prompt = "> "
		self.manager = manager

	def do_add(self, url):
		self.manager.add( url )
		return False
	
	def do_run(self, url):
		self.manager.addAndStart( url )
		return False

	def do_info(self, line):
		self.manager.printAllInfo()
		return False

	def do_EOF(self, line):
		return True


def main():
	manager = Manager()

	console = RGetConsole( manager )
	console.cmdloop()

	manager.shutdown()

if __name__ == '__main__':
	main()
