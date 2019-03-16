Like many of us, I have been generating SSL keys, CSRs, and certificates
for many many years. The best practices have evolved over the years, with
the biggest one being enforced by Chrome 58, with the subjectAlternativeName, SAN.

This script is a Python toolbox that will generate:

1. private keys
2. CSR, certificate signing request, with SAN fields.
3. self-signed certificates with SAN fields
4. local CA private key
5. local CA certificate
6. local CA signed certificates with SAN fields

The SAN fields support DNS names, IP addresses, and email addresses.

To generate a self-signed certificate and private key:

mkLocal.py --self hostname

This will make a directory, hostname, which will contain:

1. An openssl configuration file, hostname.config
2. A private key, hostname.key
3. A CSR generated from the private key and config, hostname.csr, with a common name of hostname.local
4. A self-signed certificate, hostname.cert, with a common name of hostname.local
5. A combined PEM file, hostname.pem, which contains both the certificate and private key


To generate a local CA signed certificate and private key:

mkLocal.py --ca hostname

This will make two directories, CA and hostname. CA will contain:

1. An openssl configuration file, CA.config
2. A file with the private key password, CA.codigo
3. A private key for the CA, CA.key
4. The CA's certificate, CA.cert

The CA key and certificate will be used in the future for additional signing.

The hostname directory is exactly like the self-signed case, 
except the certificate is signed by the CA key and certificate above.

To generate a private key and CSR for a foo.bar.cl in Santiago, Chile, also to be
known as www.foobar.cl, use the following command:

mkLocal.py --csr \
           --country=CL \
           --state=Santiago \
           --city=Santiago \
           --org='Foo Bar Widgets' \
           --unit='Testing Division' \
           --email=info@foobar.cl \
           --DNS=www.foobar.cl \
           --domain=bar.cl \
           foo

This will generate a directory, foo, with foo.config, foo.key, and foo.csr.

To generate a private key and self-signed certificate 
for foo.local and an IP address, 10.1.2.3:

mkLocal.py --self --IP=10.1.2.3 foo

To generate a new CSR from an existing private key:

mkLocal.py --renew hostname

Please use the --help option for additional command line options.

This script has been tested under a Mac and various flavors of Unix and Linux. 
I doubt it will run on Windows, but it should work on cygwin.

The system prerequisites are Python 3 and openssl.
