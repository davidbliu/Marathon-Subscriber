import yaml
from marathon import MarathonClient
import requests
import json
import etcd_driver
data = yaml.load(open('mesos.yaml', 'r'))
etcd_host = data['etcd']['host']
marathon_host = data['marathon']['host']
marathon_port = data['marathon']['port']
test_config = data['ingestor'][data['ingestor'].keys()[0]]

#
# launches a single app. you may need to launch several apps for fixed host groups
#
def launch_app(service_name, app_id, config, labels = [], instances = -1):
	print 'launching ' + service_name
	service_dict = config
	image = service_dict['image']
	try:
		ports = service_dict['ports'].values()
	except:
		ports = []
	if instances == -1:
		instances = 1 if not service_dict.get('instances') else service_dict.get('instances')
	cpus = 0.3 if not service_dict.get('cpus') else service_dict.get('cpus')
	mem = 512 if not service_dict.get('mem') else service_dict.get('mem')
	#
	# env variables
	#
	env = {}
	env['ETCD_HOST_ADDRESS'] = etcd_host
	#
	# add support for @LABELS
	#
	env['LABELS'] = str(labels)
	env['SERVICE_NAME'] = service_name
	# set up custom environment variables
	custom_env = service_dict.get('environment')
	if custom_env:
		for key in custom_env.keys():
			env[key] = custom_env[key]
	options = []
	constraints = []

	#
	# TODO add support for this
	#
	if service_name == "cassandra":
		options = ["-p", "7000:7000", "-p", "9042:9042", "-p", "9160:9160", "-p", "22000:22", "-p", "5000:5000"]
		ports = []
		constraints = [["hostname", "UNIQUE"]]
	if service_dict.get('volumes'):
		for volume in service_dict['volumes']:
			options.append('-v')
			options.append(volume)

	return_app = marathon_api_launch(image, options, app_id, instances, constraints, cpus, mem, env, ports)
	return return_app


def marathon_api_launch(image, options, marathon_app_id, instances, constraints, cpus, mem, env, ports):
	marathon_client = MarathonClient('http://' + str(marathon_host) + ':' + str(marathon_port))
	marathon_client.create_app(
		container = {
			"image" : str("docker:///"+image), 
			"options" : options
		},
		id = marathon_app_id,
		instances = str(instances),
		constraints = constraints,
		cpus = str(cpus),
		mem = str(mem),
		env = env,
		ports = ports #should be listed in order they appear in dockerfile
	)
	return marathon_app_id

def sync_group_config(service, labels, config):
	encoded_labels = str(sorted(labels))
	etcd_driver.set_group_config(service, encoded_labels, config)

if __name__ == "__main__":
    
    print 'hi'
    print test_config
    labels = ['testing']
    etcd_driver.create_group('ingestor', 'testing', test_config)
    sync_group_config('ingestor', labels, test_config)
    launch_app('ingestor', 'ingestorD.L-testing-D.L639d547a-753e-43be-bfe9-c10d9eb63b44D.L', test_config, labels = labels)