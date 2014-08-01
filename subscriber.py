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

#
# notify when task created/destroyed
#
@app.route('/callback', methods=['GET', 'POST'])
def callback():
	# try:
	event = request.get_json()
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
		print 'a '+str(service_name)+' container changed: status '+str(status)
		print 'reconfiguring etcd...'
		
		if int(status) == 1:
			print 'registering new container '+str(taskId)
			reg.register_new_container(taskId)
		else:
			print 'remove dead container '+str(taskId)
			reg.deregister_with_etcd(service_name, taskId)
		print 'cleaning up....'
		reg.clean_service(service_name, decoded_app_data['labels'])
		# reg.register_all()
		# print 'done'
	# except Exception as failure:
	#     print 'wut...something failed...'
	#     print failure
	return jsonify(result={"status": 200})

@app.route('/info', methods = ['GET', 'POST'])
def info():
	print 'info is not here'

	# except:
	#     print 'wut wut'
	return render_template('etcd_view.html', registered = '')

if __name__ == '__main__':

	data = None
	host = 'localhost'
	# host = socket.gethostbyname(socket.gethostname())

	marathon_url = 'http://localhost:8080'
	callback_url = 'http://localhost:5000/callback'
	print 'registering with marathon'
	m = marathon.MarathonClient(marathon_url)
	m.create_event_subscription(callback_url)
	atexit.register(on_exit, m, callback_url)

	print 'starting app on '+str(host)
	app.run(port=5000, host=host)