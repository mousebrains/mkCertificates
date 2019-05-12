#! /usr/bin/env python3
#
# Generate SSL private keys, CSRs, and certificates.
# The CA for signing CSRs can either be self-signed or a local CA.
#
# All certificates will have subject alternative names, 
# amoung other things, this makes Chrome happier.
#
# For CA see:
# https://fabianlee.org/2018/02/17/ubuntu-creating-a-trusted-ca-and-san-certificate-using-openssl-on-ubuntu/
#
# March-2019, Pat Welch, pat@mousebrains.com
#

import argparse
import os
import subprocess

configLoad0 = """
# Automatically generated

[ req ]
prompt = no
default_keyfile     = server-key.pem
distinguished_name  = subject
req_extensions      = v3_req
default_bits        = {}

[ subject ]
"""

configLoad1 = """
[ x509_ext ]
# Section x509_ext is used when generating a self-signed certificate. 
# i.e., openssl req -x509 ...

subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid,issuer

# You only need digitalSignature below. *If* you don\'t allow
#   RSA Key transport (i.e., you use ephemeral cipher suites), then
#   omit keyEncipherment because that\'s key transport.
basicConstraints    = CA:FALSE
keyUsage            = digitalSignature, keyEncipherment
subjectAltName      = @alt_names

[ v3_ca ] 
# Used for CA certificate generation
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:TRUE, pathlen:3
keyUsage               = critical, cRLSign, keyCertSign

[ v3_req ] # Used when generating a CSR. i.e., openssl req ...
basicConstraints = CA:FALSE
keyUsage         = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName   = @alt_names

[ alt_names ]
"""

def mkConfig(fn, args, host, bits):
    with open(fn, 'w') as fp:
        fp.write(configLoad0.format(bits))
        if args.country is not None: fp.write('C  = {}\n'.format(args.country))
        if args.state is not None:   fp.write('ST = {}\n'.format(args.state))
        if args.city is not None:    fp.write('L  = {}\n'.format(args.city))
        if args.org is not None:     fp.write('O  = {}\n'.format(args.org))
        if args.unit is not None:    fp.write('OU = {}\n'.format(args.unit))
        fp.write('CN = {}\n'.format(mkFQDN(host, args)))
        fp.write(configLoad1)
        fp.write('\n'.join(mkSAN(host, args)))
        fp.write('\n')

def mkFQDN(name, args):
    if args.domain is None:
        return name
    return name + "." + args.domain[0]

def addSANs(prefix, vals, offset):
    a = []
    if vals is not None:
        for i in range(len(vals)):
            a.append('{}.{} = {}'.format(prefix, i + offset, vals[i]))
    return a

def mkSAN(host, args):
    a = [];
    if args.domain is not None:
        for i in range(len(args.domain)):
            a.append('DNS.{} = {}'.format(i, host + "." + args.domain[i]))

    a.extend(addSANs('DNS', args.DNS, len(a)))
    a.extend(addSANs('IP', args.IP, 0))
    a.extend(addSANs('email', args.email, 0))
    return a
        
def mkSubject(args, commonName):
    items = [ \
            '/C={}'.format(args.country), \
            '/ST={}'.format(args.state), \
            '/L={}'.format(args.city), \
            '/O={}'.format(args.org), \
            '/OU={}'.format(args.unit)
            ]
    if commonName is not None:
        items.append('/CN={}'.format(commonName))
    return ''.join(items)

def runCmd(args, opts):
    cmd = [args.openssl]
    cmd.extend(opts)
    print(' '.join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.stdout:
        print(str(p.stdout, 'utf-8'))
    return p.returncode == 0

def mkNames(dirname, hostname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname, mode=0o700) # Exclude anybody but the owner from this directory

    return (os.path.join(dirname, '{}.config'.format(hostname)),
        os.path.join(dirname, '{}.key'.format(hostname)),
        os.path.join(dirname, '{}.csr'.format(hostname)),
        os.path.join(dirname, '{}.cert'.format(hostname)))

def mkCA(args):
    (config, key, csr, cert) = mkNames(args.caDir, args.caPrefix)
    codigo = os.path.join(args.caDir, '{}.codigo'.format(args.caPrefix))
    if os.path.exists(config) and \
            os.path.exists(key) and \
            os.path.exists(cert) and \
            os.path.exists(codigo):
        return (key, cert, codigo)

    mkConfig(config, args, args.caPrefix, args.cabits)
    runCmd(args, ['rand', '-out', codigo, '-base64', str(args.cacodigolen)])
    os.chmod(codigo, 0o600) # Make private to owner
    runCmd(args, ['genrsa', '-out', key, '-aes256', '-passout', 'file:{}'.format(codigo), 
        str(args.cabits)])
    os.chmod(key, 0o600) # Make private to owner
    runCmd(args, ['req', \
            '-new', \
            '-x509', \
            '-extensions', 'v3_ca', \
            '-config', config, \
            '-days', str(args.caDays), \
            '-key', key, \
            '-passin', 'file:{}'.format(codigo), \
            '-sha256', \
            '-out', cert])
    if args.verbose:
        runCmd(args, ['x509', '-text', '-noout', '-in', cert])
    return (key, cert, codigo)

def mkPEM(cert, key): # Generate combined PEM file
    pem = os.path.commonprefix([cert, key]) + 'pem'
    with open(pem, 'w') as ofp:
        for fn in [cert, key]:
            with open(fn, 'r') as ifp:
                ofp.write(ifp.read())
    os.chmod(pem, 0o600) # Only visible to the owner

parser = argparse.ArgumentParser()
parser.add_argument('hosts', nargs='+', 
        help='Hostnames, without suffix, to generate keys/csr/certs for')
parser.add_argument('--bits', default=4096, help='# of bits to generate keys with')
parser.add_argument('--days', default=3650, help='# of days certificates are valid for')
parser.add_argument('--DNS', action='append', help='subjectAltNames DNS entries')
parser.add_argument('--IP', action='append', help='subjectAltNames IP addresses')
parser.add_argument('--email', action='append', help='subjectAltNames emails')
parser.add_argument('--domain', action='append', help='domain name to generate FQDN')
parser.add_argument('--openssl', default='/usr/bin/openssl', help='openssl command to use')
parser.add_argument('--country', help='Subject country')
parser.add_argument('--state', help='Subject state')
parser.add_argument('--city', help='Subject city/locality')
parser.add_argument('--org', help='Subject organization')
parser.add_argument('--unit', help='Subject orgainzational unit')

grp = parser.add_mutually_exclusive_group(required=True)
grp.add_argument('--self', action='store_true', help='Generate key and self-signed certificate')
grp.add_argument('--csr', action='store_true', help='Generate key and CSR')
grp.add_argument('--renew', action='store_true', help='Generate CSR from an existing key')
grp.add_argument('--ca', action='store_true', help='Generate key and local CA signed certificate')

parser.add_argument('--caDir', default='CA', help='Directory to store CA in')
parser.add_argument('--caPrefix', default='CA', help='Directory to store CA in')
parser.add_argument('--caDays', default=7300, help='# of days to make CA certificate valid for')
parser.add_argument('--cabits', default=4096, help='# of bits to make CA key')
parser.add_argument('--cacodigolen', default=96, help='# of characters in CA password')

parser.add_argument('--verbose', action='store_true', help='More diagnostics')

args = parser.parse_args()

for host in args.hosts:
    print('Working on', host)

    if args.ca:
        (caKey, caCert, caCodigo) = mkCA(args)

    (config, key, csr, cert) = mkNames(host, host)

    if not args.renew: # Generate a new key
        runCmd(args, ['genrsa', '-out', key, str(args.bits)])
        os.chmod(key, 0o600) # Make private to owner

    if args.renew and not os.path.exists(key):
        print('ERROR:', key, 'does not exist')
        continue

    mkConfig(config, args, host, args.bits)

    runCmd(args, ['req', \
            '-new', \
            '-extensions', 'v3_req', \
            '-config', config, \
            '-sha256', \
            '-key', key, \
            '-out', csr])

    if args.csr or args.renew: # Only make through a CSR
        if args.verbose: # Print out CSR
            runCmd(args, ['req', '-text', '-noout', '-in', csr])
        continue

    # Sign the CSR, either self or with a local CA

    opts = ['x509', \
            '-req', \
            '-extensions', 'v3_req', \
            '-extfile', config, \
            '-days', str(args.days), \
            '-sha256', \
            '-in', csr, \
            '-out', cert]

    if args.self: # Make a self-signed certificate
        opts.extend(['-signkey', key])
    else: # Sign with my CA
        opts.extend([ \
            '-CA', caCert, \
            '-CAkey', caKey, \
            '-passin', 'file:{}'.format(caCodigo), \
            '-CAcreateserial'])
    runCmd(args, opts) # Sign the csr, either self or my CA

    if args.verbose: # Print out the signed certificate
        runCmd(args, ['x509', '-text', '-noout', '-in', cert])

    if os.path.exists(key) and os.path.exists(cert): # Make combined PEM file
        mkPEM(cert, key)
