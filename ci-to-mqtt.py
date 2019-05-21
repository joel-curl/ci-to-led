#!/usr/bin/python3

import paho.mqtt.client as mqtt
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

class MqttProxy():
	def __init__(self, broker, topic):
		self.client = mqtt.Client()
		self.broker = broker
		self.topic = topic
		self.logger = logging.getLogger('MQTT')

	def send(self, message):
		self.logger.info('Sending message')
		self.logger.debug(message)
		self.client.connect(self.broker)
		self.client.publish(self.topic, message)

class WebhookHandler(BaseHTTPRequestHandler):
	mqttc = MqttProxy('localhost', 'build')

	def do_POST(self):
		request_body = self.rfile.read(int(self.headers.get('Content-Length')))

		logger = logging.getLogger('HTTP')
		logger.info('Received POST')
		logger.debug(request_body)

		self.mqttc.send(request_body)
		self.send_response(200)
		self.end_headers()
		
class WebhookMonitor():
	handler = None

	def __init__(self, webhook_handler):
		self.handler = webhook_handler

	def run(self, port):
		server_address = ('', port)
		httpd = HTTPServer(server_address, self.handler)
		httpd.serve_forever()

logging.basicConfig(level=logging.INFO)
webhook_monitor = WebhookMonitor(WebhookHandler)
webhook_monitor.run(9999)

