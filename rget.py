#!/usr/bin/env python

import subprocess
import re
from threading import Thread
from cmd import Cmd
import urlparse

class WGetInfo(object):
	STATUS_REGEX = re.compile("[ \t]*(?P<data>[0-9]+)(?P<data_unit>[ KMG])[ '.']*(?P<percent>[0-9]+)%[ ]*(?P<speed>[0-9]+)(?P<speed_unit>[ KMG])[ =](?P<time>[0-9dhms ]+)")
	INFO_REGEX = re.compile("Length\: (?P<size>[0-9]+) \((?P<size_hr>[0-9]+)(?P<size_hr_unit>[ KMG])\) \[(?P<type>.*)\]")
 
 	FACTORS = {
		' ': 1,
		'K': 1024,
		'M': 1024*1024,
		'G': 1024*1024*1024
	}

	def __init__(self):
		self.completeData = 0
		self.data = 0
		self.process = 0
		self.speed = 0
		self.time = ''
		self.type = ''
	
	def update(self, line):
		
		r = WGetInfo.STATUS_REGEX.search(line)
		if r != None:
			self.status_update(r.groupdict())
			return

		r = WGetInfo.INFO_REGEX.search(line)
		if r != None:
			self.info_update(r.groupdict())
			return

	def info_update(self, size):
		self.completeData = size['size']
		self.type = size['type']

	def status_update(self, status):
		self.data = int(status['data']) * WGetInfo.FACTORS[status['data_unit']]
		self.process = int(status['percent'])
		self.speed = int(status['speed']) * WGetInfo.FACTORS[status['speed_unit']]
		self.time = status['time']

	def status_update_finished(self):
		self.data = self.completeData
		self.process = 100
		self.speed = 0
		self.time = '0s'
	
	def __str__(self):
		return "{0}/{1} ({2} %) ETA: {3}".format(self.data, self.completeData, self.process, self.time)
	
	def detail(self):
		return "{0}/{1} ({2} %)\nETA: {3}\nCurrent speed: {4}/s\nType: {5}".format(
			self.data, self.completeData,
			self.process,
			self.time,
			self.speed,
			self.type
		)

class WGetProcess(Thread):
	STAT_IDLE = 0
	STAT_DL = 1
	STAT_FIN_GOOD = 2
	STAT_FIN_BAD = 3
	STAT_FIN_USER = 4

	def __init__(self, url, outputDir = None, cont = False, post_hook = None, pre_hook = None):
		Thread.__init__(self, name='WGet ' + url)
		self.url = url
		self.outputDir = outputDir
		self.cont = cont
		self.info = WGetInfo()
		self.running = False
		self.status = WGetProcess.STAT_IDLE
		self.exit_status = None
		self.finished = False
		self.post_hook = post_hook
		self.pre_hook = pre_hook

	def getParams(self):
		params = ['wget', '--progress=dot']

		if self.outputDir != None:
			params.append('-P')
			params.append(self.outputDir)

		if self.cont:
			params.append('-c')

		params.append(self.url)

		return params

	def run(self):
		self.running = True
		self.finished = False

		params = self.getParams()
		
		self.proc = subprocess.Popen(params, stderr=subprocess.PIPE, env= {'LANG': 'C'})

		if self.pre_hook != None:
			self.pre_hook(self)
	
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
				self.info.status_update_finished()
				if self.post_hook != None:
					self.post_hook(self)
			else:
				self.status = WGetProcess.STAT_FIN_BAD

		self.finished = True

class Manager(object):

	STATUS_NAMES = {
		WGetProcess.STAT_IDLE: "Idle",
		WGetProcess.STAT_DL: "Downloading",
		WGetProcess.STAT_FIN_USER: "Abortet by user",
		WGetProcess.STAT_FIN_GOOD: "Done",
		WGetProcess.STAT_FIN_BAD: "Exited abnormally"
	}

	def __init__(self):
		self.processes = []

	def _dl_pre_hook(self, process):
		print "Started {0}".format(process.url)

	def _dl_post_hook(self, process):
		print "Finished {0}".format(process.url)

	def add(self, url, outputDir = None, cont = False):
		new_process = WGetProcess( 
			url, 
			outputDir = outputDir, 
			cont = cont,
			pre_hook = self._dl_pre_hook,
			post_hook = self._dl_post_hook
			)
		self.processes.append( new_process )
		return new_process

	def addAndStart(self, url, outputDir = None, cont = False):
		process = self.add(url, outputDir, cont)
		process.start()
		return process

	def getProcessesByUrl(self, url):
		return [p for p in self.processes if p.url == url]

	def stop(self, id = None, url = None): #TODO Exceptions for errorhandling
		if id == None and url == None:
			return False

		if id != None:
			return self.stopById(id)
		else:
			return self.stopByUrl(url)
		
	def stopById(self, id):
		if id < 0 or id >= len(self.processes):
			return False
		if not self.processes[id].running:
			return False

		self.processes[id].running = False
		return True

	def stopByUrl(self, url):
		processes = self.getProcessesByUrl(url) 

		if len(processes) == 0:
			return False

		for p in processes:
			if p.running:
				p.running = False

		return True
		
	def start(self, id = None, url = None):
		if id == None and url == None:
			return False

		if id != None:
			return self.startById(id)
		else:
			return self.startByUrl(url)		
	
	def startById(self, id):
		if id < 0 or id >= len(self.processes):
			return False
		if self.processes[id].status != WGetProcess.STAT_IDLE:
			return False

		self.processes[id].start()
		return True

	def startByUrl(self, url):
		processes = self.getProcessesByUrl(url)

		if len(processes) == 0:
			return False
		
		for p in processes:
			if p.status == WGetProcess.STAT_IDLE:
				p.start()

		return True

	def startAll(self):
		started = False
		for p in [p for p in self.processes if p.status == WGetProcess.STAT_IDLE]:
			started = True
			p.start()

		return started

	def removeFinished(self):
		for p in [p for p in self.processes if p.finished]:
			self.processes.remove(p)

	def remove(self, id = None, url = None):
		if id == None and url == None:
			return False

		if id != None:
			return self.removeById(id)
		else:
			return self.removeByUrl(url)		

	def removeById(self, id):
		if id < 0 or id >= len(self.processes):
			return False

		if self.processes[id].status == WGetProcess.STAT_DL:
			self.stopById(id)
			
		del self.processes[id]
		return True		
	
	def removeByUrl(self, url):
		processes = self.getProcessesByUrl(url)

		if len(processes) == 0:
			return False
		
		for p in processes:
			if p.status == WGetProcess.STAT_DL:
				p.running = False

			self.processes.remove(p)

		return True
		
	def printProcessInfo(self,i,p):
		print '{0:3d}\t{1}\t{2}\t{3}'.format(i, Manager.STATUS_NAMES[p.status], p.info, p.url)

	def listProcesses(self):
		if len(self.processes) > 0:
			for i, p in enumerate(self.processes):
				self.printProcessInfo(i,p)
		else:
			print "No downloads in list."

	def isValidId(self, id):
		return id >= 0 or id < len(self.processes)

	def printDetail(self, id = None, url = None):
		if id == None and url == None:
			return False

		processes = []

		if id != None and self.isValidId(id):
			processes = [self.processes[id]]
		else:
			processes = self.getProcessesByUrl(url)
			
		for i,p in enumerate(processes):
			print '{0:3d}\t{1}\t{2}'.format(i, Manager.STATUS_NAMES[p.status], p.url)
			print p.info.detail()

	
	def shutdown(self):
		for p in self.processes:
			if p.running == True:
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

	def do_startAll(self, line):
		self.manager.startAll()
		return False

	def do_start(self, id):
		success = False

		try:
			success = self.manager.start(id = int(id))
		except ValueError:
			success = self.manager.start(url = id)

		if not success:
			print "Could not start Process #", id

		return False

	def do_stop(self, id):
		success = False

		try:
			success = self.manager.stop(id = int(id))
		except ValueError:
			success = self.manager.stop(url = id)

		if not success:
			print "Could not stop Process #", id

		return False

	def do_gc(self, line):
		return self.do_removeFinished(line)

	def do_removeFinished(self, line):
		self.manager.removeFinished()
		return False

	def do_rm(self, id_url):
		return self.do_remove(id_url)

	def do_remove(self, id):
		success = False

		try:
			success = self.manager.remove(id = int(id))
		except ValueError:
			success = self.manager.remove(url = id)

		if not success:
			print "Could not remove Process #", id

		return False

	def do_detail(self, id_url):
		try:
			self.manager.printDetail(id = int(id_url))
		except ValueError:
			self.manager.printDetail(url = int(id_url))
			
		return False

	def default(self, line):
		self.manager.add( line )
		return False

	def emptyline(self):
		if not self.manager.startAll():
			self.manager.listProcesses()
		return False

	def do_dl(self, url):
		self.manager.addAndStart( url )
		return False

	def do_ls(self, line):
		self.manager.listProcesses()
		return False

	def do_EOF(self, line):
		return True

	def do_exit(self, line):
		return True


def main():
	manager = Manager()

	console = RGetConsole( manager )
	console.cmdloop()

	manager.shutdown()

if __name__ == '__main__':
	main()
