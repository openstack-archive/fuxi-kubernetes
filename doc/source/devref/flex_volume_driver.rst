..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

Flex Volume Driver
==================

As the spec`[1]`_ introduced, FlexVolume`[2]`_ driver will implement the driver
interfaces of FlexVolume plugin to enable Kubelet to consume persistent
volumes. Each driver will be loaded when Kubelet starts and be used as
the standalone FlexVolume plugin, which means that Kubelet may start
several FlexVolume plugins and each plugin binds one driver. 

In fuxi-kubernetes, FlexVolume driver consists of four components.

.. figure:: https://raw.githubusercontent.com/openstack/fuxi-kubernetes/master/doc/images/flex_volume_driver.png
    :alt: FlexVolume Driver
    :align: center

1. **Shell**:
FlexVolume plugin will communicate with driver by 'call-out'. So, to plguin,
the driver should be an executable file which receives each command and
returns corresponding results. To Cinder and Manila, there is a shell
file for each of them to do this work respectively.

2. **Service**:
The real driver runs as a service and locates at the work node. It
integrates Cinder and Manila to supply volume for Pod.

3. **Client**:
'Shell' will pass the commands to 'Service' by 'Client'.

4. **Host**:
The driver runs on the work node which may be baremetal or vitual machine.
It needs know the informations of work node to supply volume for Pod. 'Host'
stands for the work node and supply relevant informations, such as host name,
connector which is used to connect volumes.


References
----------
_`[1]`: https://docs.openstack.org/developer/kuryr-kubernetes/specs/pike/fuxi_kubernetes.html
_`[2]`: https://github.com/kubernetes/community/blob/master/contributors/devel/flexvolume.md
