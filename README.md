marathon-subscriber
===================

subscriber to marathon for docker service discovery

# Getting started

set environment variables for `ETCD_HOST`, `MARATHON_HOST`, `CONTAINER_HOST_ADDRESS`, `CONTAINER_HOST_PORT`
* `ETCD_HOST` is etcd host address
* `MARATHON_HOST` is marathon host address
* `CONTAINER_HOST_ADDRESS` is the public ip of the host you are running subscriber on
* `CONTAINER_HOST_PORT` is the external (host) port you have mapped to container  port 5000

### example
`docker run -t -p 5000:5000 -e ETCD_HOST={{etcd_host_ip}} -e MARATHON_HOST={{marathon_host_ip}} -e 
CONTAINER_HOST_ADDRESSS={{public_host_ip}} -e CONTAINER_HOST_PORT=5000 subscriber`

# In progress

__decouple subscriber from marathon__. copies of subscriber will live on each mesos slave and update configuration when detect
containers deployed on that slave. this solves N to 1 problem.
