#!/usr/bin/python3

import yaml
from enum import Enum
from gpiozero import LED
import paho.mqtt.client as mqtt
import logging

RED_CHAN = 3
GREEN_CHAN = 2
MQTT_BROKER_HOST = '3.216.43.142'
MQTT_TOPIC = 'build'

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
		try:
			json_dict = yaml.load(json_str) # works for nonstandard json
			status = self.status.get(json_dict['commit_status']['state'], Status.INIT)
		except:
			status = Status.INIT
		return status

class RedGreenLedNotification():
	def __init__(self, red_chan, green_chan):
		self.red = LED(red_chan)
		self.green = LED(green_chan)
		self.logger = logging.getLogger('LED')
		self.on_default()

	def on_default(self):
		self.logger.info('default state')
		self.red.on()
		self.green.off()

	def on_inprogress(self):
		self.logger.info('inprogress state')
		self.red.off()
		self.green.blink()

	def on_success(self):
		self.logger.info('success state')
		self.red.off()
		self.green.on()

	def on_failure(self):
		self.logger.info('failure state')
		self.red.blink()
		self.green.off()

class NotificationManager():
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

class MqttListener():
	def __init__(self, broker, topic, event_manager):
		self.manager = event_manager
		self.broker = broker
		self.topic = topic
		self.client = mqtt.Client()
		self.logger = logging.getLogger('MQTT')

	@staticmethod
	def on_message(client, userdata, message):
		userdata.logger.info('Received message')
		userdata.logger.debug(message.payload)
		userdata.manager.update(message.payload)

	def listen(self):
		self.client.connect(self.broker)
		self.client.user_data_set(self)
		self.client.on_message=self.on_message
		self.client.subscribe(self.topic)
		self.logger.info('Connected to {}, listening to {}'.format(self.broker, self.topic))
		self.client.loop_forever()

logging.basicConfig(level=logging.INFO)
manager = NotificationManager(RedGreenLedNotification(RED_CHAN, GREEN_CHAN))
mqtt_listener = MqttListener(MQTT_BROKER_HOST, MQTT_TOPIC, manager)
mqtt_listener.listen()

