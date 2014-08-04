import yaml
from marathon import MarathonClient
import sys
import etcd
import ast
import etcd_driver
import os
# from Entities import *
# data = yaml.load(open('mesos.yaml', 'r'))



etcd_host = os.environ['ETCD_HOST_ADDRESS']
etcd_port = 4001
marathon_host = os.environ['MARATHON_HOST']
marathon_port = '8080'

marathon_client = MarathonClient('http://' + str(marathon_host) + ':' + str(marathon_port))
etcd_client = etcd.Client(host = str(etcd_host), port = int(etcd_port))
#
# Registers a container with etcd
#
def register_with_etcd(service, name, host, port_mapping, labels = []):
  # throw an error if cannot connect to client?
  encoded_labels = encode_labels(labels)
  instance_dict = {}
  instance_dict['service_name'] = service
  instance_dict['instance_name'] = name
  instance_dict['instance_host'] = host
  instance_dict['port_mapping'] = port_mapping
  instance_dict['labels'] = labels

  # etcd_key = "/services/"+service+'/'+encoded_labels+'/containers/'+name+'/info'
  # try:
  #   old_dict = etcd_client.read(etcd_key).value
  # except:
  #   new_dict = {}
  #   etcd_client.write(etcd_key, new_dict)

  etcd_driver.set_container_info(service, encoded_labels, name, instance_dict)

#
# remove a container from etcd
#
def deregister_with_etcd(service, name):
	# print 'deregistering '+str(name)
	app_data = decode_marathon_id(name)
	# print 'labels are '+str(app_data['labels'])
	etcd_driver.deregister_container(service, encode_labels(app_data['labels']), name)



#
# makes sure there are no tasks in etcd that do not correspond with tasks known by marathon
# basically syncing up, no actual task removal involved.
#
def clean_service(service):
	service_tasks = marathon_client.list_tasks()
	service_task_names = map(lambda x: x.id, service_tasks)

	#
	# loop through etcd instances, if name not in tasks, clean up
	#
	service_name = service
	etcd_container_names = etcd_driver.get_service_containers(service_name)
	# print etcd_container_names
	for container_name in etcd_container_names:
		if container_name not in service_task_names:
			deregister_with_etcd(service, container_name)
	#
	# remove groups that no longer have containers
	#
	for group in etcd_driver.get_service_groups(service):
		if len(etcd_driver.get_group_container_names(service, group)) == 0:
			etcd_driver.remove_group(service, group)

	#
	# if this service no longer has containers, remove it
	#
def clean_all():
	services = etcd_driver.get_service_names()
	for serv in services:
		clean_service(serv)	

def get_task(taskId):
	all_tasks = marathon_client.list_tasks()
	this_task = None
	#
	# also cleans up tasks
	#
	for task in all_tasks:
		if task.id == taskId:
			this_task = task
	return this_task


def encode_labels(labels):
	return str(sorted(labels)).replace(' ', '')

def decode_marathon_id(marathon_id, id_separator = 'D.L'):
    # split up id
    id_split = marathon_id.split(id_separator)
    service_name = str(id_split[0])
    labels = ast.literal_eval('['+id_split[1].replace("-", "'").replace(".", ",")+']')
    version = str(id_split[2])
    return {'service':service_name, 'labels':labels, 'version':version}


def register_new_container(task_id):

	task = get_task(task_id)
	if task.started_at:
		app_id = task.app_id
		app_data = decode_marathon_id(app_id)
		original_labels = app_data['labels']
		labels = encode_labels(original_labels)
		service = app_data['service']
		container_name = task_id

		config_key = '/services/'+service+'/'+labels+'/config'
		config = ast.literal_eval(etcd_client.read(config_key).value)

		lg_key = labels
		host = task.host
		name = task.id 
		port_mapping = {}
		if 'ports' in config.keys():
			ports = config['ports'].values()
			ports.sort()
			port_names = []
			for port in ports:
				port_names.append(reverse_map(config['ports'], port))
			for index in range(0, len(port_names)):
				port_mapping[port_names[index]] = {}
				port_mapping[port_names[index]]["external"] = ('0.0.0.0', str(task.ports[index])+'/tcp')
				port_mapping[port_names[index]]["exposed"] = str(ports[index]) + '/tcp'
		# print service
		# print name
		# print host
		# print port_mapping
		register_with_etcd(service, name, host, port_mapping, original_labels)
	else:
		print 'task was staged but not started...'

def reverse_map(d, value):
	for key in d.keys():
		if d[key] ==  value:
			return key
	return None


if __name__ == "__main__":
    args = sys.argv
    print 'Welcome Master Liu'
    command = args[1]
    if command == 'all':
    	register_all()