To install a private key and certificate on a Ubiquiti airOS device:

1. Generate a private key and certificate, say for nanobeam01.local at 192.168.99.98 using a local CA:

mkLocal.py --ca --IP=192.168.99.98 nanobeam01

2. Using scp, copy the private key, certificate, and PEM file to the airOS device

scp nanobeam01.key ubnt@192.168.99.98:/etc/persistent/https/server.key
scp nanobeam01.cert ubnt@192.168.99.98:/etc/persistent/https/server.crt
scp nanobeam01.pem ubnt@192.168.99.98:/etc/server.pem

3. Now login into the airOS device and save the new information to flash:

ssh ubnt@192.168.99.98
cfgmtd -w -p /etc/
/usr/etc/rc.d/rc.softrestart save
reboot

I'm not sure if both cfgmtd and rc.softrestart are required, but it works.
