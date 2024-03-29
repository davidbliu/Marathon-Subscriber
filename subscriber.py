import argparse
import atexit
import sys
import urlparse
import yaml
from flask import Flask, request, jsonify, render_template
import marathon
import urllib2
import etcd
import socket
import os
import shutil
import ast
import json
import etcd_driver
#
# for storing events (TODO)
#

app = Flask(__name__)

# re-initialize later
events = None
event_store = None
data = None
marathon_client = None

def on_exit(marathon_client, callback_url):
	print 'exiting app.....'
	marathon_client.delete_event_subscription(callback_url)
@app.route('/cleanup', methods=['GET','POST'])
def cleanup():
	services = etcd_driver.get_service_names()
	for service in services:
		reg.clean_service(service)
	return jsonify(result={"status": 200})
#
# notify when task created/destroyed
#
@app.route('/callback', methods=['GET', 'POST'])
def callback():
	# try:

	event = request.get_json()
	# print event
	if event['eventType'] == "status_update_event":

		status = event['taskStatus']
		host = event['host']
		taskId = event['taskId']
		appId = event['appID']

		import register as reg
		# service_name = reg.decode_marathon_id(appId)['service']
		decoded_app_data = reg.decode_marathon_id(appId)
		service_name = decoded_app_data['service']
		# 
		# status 1 means running 2 means killed
		# print 'a '+str(service_name)+' container changed: status '+str(status)
		# print 'reconfiguring etcd...'
		
		if int(status) == 1:
			print 'STARTED '+str(taskId)
			reg.register_new_container(taskId)
		else:
			print 'KILLED '+str(taskId)
			reg.deregister_with_etcd(service_name, taskId)
		print 'CLEANING UP...'
		reg.clean_service(service_name)
	
		# reg.register_all()
		# print 'done'
	# except Exception as failure:
	#     print 'wut...something failed...'
	#     print failure
	return jsonify(result={"status": 200})

if __name__ == '__main__':

	data = None
	# host = 'localhost'
	host = socket.gethostbyname(socket.gethostname())

	# marathon_url = 'http://localhost:8080'
	marathon_host = os.environ['MARATHON_HOST']
	marathon_port = '8080'
	marathon_url = 'http://'+marathon_host+':'+marathon_port

	# marathon_url = os.environ['MARATHON_URL']
	host_address = os.environ.get('CONTAINER_HOST_ADDRESS')
	host_port = os.environ.get('CONTAINER_HOST_PORT')
	if host_address and host_port:
		callback_url = 'http://'+str(host_address)+':'+str(host_port)+'/callback'
	else:
		print 'plz provide correct env variables dawg'
		callback_url = 'http://localhost:5000/callback'
	print 'registering with marathon'
	m = marathon.MarathonClient(marathon_url)
	m.create_event_subscription(callback_url)
	atexit.register(on_exit, m, callback_url)

	import register as reg
	try:
		reg.clean_all()
	except:
		print 'no services created yet'
	print 'starting app on '+str(host)
	app.run(port=5000, host=host)