import etcd
import ast
import os
etcd_host_address = os.environ['ETCD_HOST_ADDRESS'] 
etcd_client = etcd.Client(host=etcd_host_address, port=4001)
#
# create no matter what
#
def create_service(service_name):
	service_string = '/services/'+service_name
	if service_exists(service_name):
		print 'service already exists...removing service'
		etcd_client.delete(service_string, recursive=True)
	etcd_client.write(service_string, None, dir=True)

#
# create no matter what (force)
#
def create_group(service_name, encoded_labels, config):
	group_string = '/services/'+service_name+'/'+encoded_labels
	if group_exists(service_name, encoded_labels):
		print 'group already exists...deleting group'
		etcd_client.delete(group_string, recursive=True)
	etcd_client.write(group_string,None, dir=True)
	etcd_client.write(group_string+'/config', config)
	etcd_client.write(group_string+'/containers', None, dir=True)

	
def service_exists(service_name):
	if '/services/'+service_name in etcd_client:
		return True
	return False

def group_exists(service_name, encoded_labels):
	group_key = '/services/'+service_name+'/'+encoded_labels
	if group_key in etcd_client:
		return True
	return False

def get_service_names():
	names = []
	for s in etcd_client.read('/services').children:
		names.append(str(s.key.replace('/services', '').replace('/','')))
	return names

def get_service_groups(service_name):
	groups = []
	for s in etcd_client.read('/services/'+service_name).children:
		groups.append(str(s.key.replace('/services/'+service_name, '').replace('/','')))
	return groups


def get_service_containers(service_name):
	all_containers = []
	groups = get_service_groups(service_name)
	for group in groups:
		containers = get_group_container_names(service_name, group)
		all_containers += containers
	return all_containers
	
def get_group_config(service_name, encoded_labels):
	group_key = '/services/'+service_name+'/'+encoded_labels
	return ast.literal_eval(etcd_client.read(group_key+'/config').value)

def set_group_config(service_name, encoded_labels, config):
	group_key = '/services/'+service_name+'/'+encoded_labels
	etcd_client.write(group_key+'/config', config)

def get_group_container_names(service_name, encoded_labels):
	containers = []
	containers_root_key = '/services/'+service_name+'/'+encoded_labels+'/containers'
	for c in etcd_client.read(containers_root_key).children:
		container_string = str(c.key.split('/')[-1])
		if container_string != 'containers':
			containers.append(container_string)
	return containers

def container_exists(service_name, encoded_labels, container_name):
	container_key = '/services/'+service_name+'/'+encoded_labels+'/containers/'+container_name
	if container_key in etcd_client:
		return True
	return False

def get_container_info(service_name, encoded_labels, container_name):
	container_info_key = '/services/'+service_name+'/'+encoded_labels+'/containers/'+container_name+'/info'
	return ast.literal_eval(etcd_client.read(container_info_key).value)

def set_container_info(service_name, encoded_labels, container_name, info):
	container_info_key = '/services/'+service_name+'/'+encoded_labels+'/containers/'+container_name+'/info'
	etcd_client.write(container_info_key, info)
#
# registers container regardless of whether service or group exists
#
def register_container(service_name, encoded_labels, container_name, info):
	container_key = '/services/'+service_name+'/'+encoded_labels+'/containers/'+container_name
	if container_exists(service_name, encoded_labels, container_name):
		etcd_client.delete(container_key)
	etcd_client.write(container_key+'/info', info)

def deregister_container(service_name, encoded_labels, container_name):
	print 'im about to deregister your container'
	print encoded_labels
	container_key = '/services/'+service_name+'/'+encoded_labels+'/containers/'+container_name
	print container_key
	etcd_client.delete(container_key, recursive=True)
	# print 'this does not /work'

if __name__ == "__main__":

	# create_service('test')
	# create_group('test', 'test-group', {'hello':'pig'})
	# print get_service_names()
	# print get_group_config('test','test-group')
	# register_container('test','test-group', 'test-container', 'random-info')
	# print get_group_container_names('test','test-group')
	# print get_service_groups('test')
	# print get_container_info('test', 'test-group', 'test-container')vice

	for s in get_service_names():
		etcd_client.delete('/services/'+s, recursive=True)
