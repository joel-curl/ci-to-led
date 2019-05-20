#!/usr/bin/python3

import yaml
from enum import Enum
from gpiozero import LED
from http.server import HTTPServer, BaseHTTPRequestHandler

class Status(Enum):
	INIT = 0
	SUCCESSFUL = 1
	INPROGRESS = 2
	FAILED = 3

class StatusFactory():

	status = {
		'SUCCESSFUL': Status.SUCCESSFUL,
		'INPROGRESS': Status.INPROGRESS,
		'FAILED': Status.FAILED,
	}

	@classmethod
	def json(self, json_str):
		# todo handle exceptions
		json_dict = yaml.load(json_str) # works for nonstandard json
		return self.status.get(json_dict['commit_status']['state'], Status.INIT)

class RedGreenLedNotification():
	def __init__(self, red_chan, green_chan):
		self.red = LED(red_chan)
		self.green = LED(green_chan)
		self.on_default()

	def on_default(self):
		self.red.on()
		self.green.off()

	def on_inprogress(self):
		self.red.off()
		self.green.blink()

	def on_success(self):
		self.red.off()
		self.green.on()

	def on_failure(self):
		self.red.blink()
		self.green.off()

class NotificationManager():
	notification = None
	status_action = {}

	def __init__(self, notification_handler):
		self.notification = notification_handler
		self.status_action = {
			Status.INIT: self.notification.on_default,
			Status.INPROGRESS: self.notification.on_inprogress,
			Status.SUCCESSFUL: self.notification.on_success,
			Status.FAILED: self.notification.on_failure,
		}
		self.notification.on_default

	def update(self, status_obj):
		status = StatusFactory.json(status_obj)
		action = self.status_action.get(status, self.notification.on_default)
		action()

class WebhookHandler(BaseHTTPRequestHandler):
	manager = NotificationManager(RedGreenLedNotification(3,2))

	def do_POST(self):
		request_body = self.rfile.read(int(self.headers.get('Content-Length')))
		self.manager.update(request_body)
		self.send_response(200)
		self.end_headers()
		
		
class WebhookMonitor():
	handler = None

	def __init__(self, webhook_handler):
		self.handler = webhook_handler

	def get_manager(self):
		return self.manager

	def run(self, port):
		server_address = ('', port)
		httpd = HTTPServer(server_address, self.handler)
		httpd.serve_forever()

webhook_monitor = WebhookMonitor(WebhookHandler)
webhook_monitor.run(8888)

