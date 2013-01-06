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

	def __init__(self, url, outputDir = None, cont = False):
		Thread.__init__(self, name='WGet ' + url)
		self.url = url
		self.outputDir = outputDir
		self.cont = cont
		self.info = WGetInfo()
		self.running = False
		self.status = WGetProcess.STAT_IDLE
		self.exit_status = None

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

	STATUS_NAMES = {
		WGetProcess.STAT_IDLE: "Idle",
		WGetProcess.STAT_DL: "Downloading",
		WGetProcess.STAT_FIN_USER: "Abortet by user",
		WGetProcess.STAT_FIN_GOOD: "Done",
		WGetProcess.STAT_FIN_BAD: "Exited abnormally"
	}

	def __init__(self):
		self.processes = []

	def add(self, url, outputDir = None, cont = False):
		new_process = WGetProcess( url, outputDir = outputDir, cont = cont )
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
			if p.status != WGetProcess.STAT_IDLE:
				p.start()

		return True

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

	def listProcesses(self):
		if len(self.processes) > 0:
			print '  id\tstatus\t\tinfo\t\turl'
			for i, p in enumerate(self.processes):
				print '{0:3d}\t{1}\t\t{2}\t\t{3}'.format(i, Manager.STATUS_NAMES[p.status], p.info, p.url)
		else:
			print "No downloads in list."
	
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
			print "Could not start Process #", id

		return False

	def do_remove(self, id):
		success = False

		try:
			success = self.manager.remove(id = int(id))
		except ValueError:
			success = self.manager.remove(url = id)

		if not success:
			print "Could not start Process #", id

		return False

	def do_run(self, url):
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
