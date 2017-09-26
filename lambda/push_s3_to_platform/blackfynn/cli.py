# -*- coding: utf-8 -*-
"""
Blackfynn Client

Usage:
  bf upload [options] <destination> <file> [<file>...]
  bf append [options] <destination> <file> [<file>...]
  bf search [options] <term> [<term>...]
  bf datasets [options]
  bf dataset [options] <dataset> [<command>] [<action>] [<action-args>...]
  bf create [options] collection <destination> <name>
  bf create [options] dataset <name>
  bf delete [options] <item>
  bf show [options] <item> 
  bf orgs [options]
  bf env [options]
  bf version

Options
  -h --help       Show help.
  --user=<user>   Email/username
  --pass=<pass>   Password
  --host=<host>   Blackfynn host
  --org=<org>     Set organization context

"""
import sys, os
from docopt import docopt

# blackfynn
import blackfynn
from blackfynn import Blackfynn, Collection, Dataset, settings
from blackfynn.models import BaseNode

def blackfynn_cli():
    args = docopt(__doc__)

    if args['version']:
        print "version: {}".format(blackfynn.__version__)

    email = args['--user'] if args['--user'] is not None else settings.api_user
    passw = args['--pass'] if args['--pass'] is not None else settings.api_pass
    host  = args['--host'] if args['--host'] is not None else settings.api_host
    org   = args['--org']

    try:
        bf = Blackfynn(email=email, password=passw, host=host)
    except:
        print "Unable to connect to to Blackfynn using specified user/password."
        return

    if args['orgs']:
        for o in bf.organizations():
            print " * {} (id: {})".format(o.name, o.id)

    if org is not None:
        try:
            bf.set_context(org)
        except:
            print 'Error: Unable to set context to "{}"'.format(org)
            return

    if args['show']:
        item = bf.get(args['<item>'])
        print item
        if hasattr(item, 'items'):
            print "CONTENTS:"
            for i in item.items:
                print " * {}".format(i)
        if hasattr(item, 'channels'):
            print "CHANNELS:"
            for ch in item.channels:
                print " * {} (id: {})".format(ch.name, ch.id)

    elif args['search']:
        terms = ' '.join(args['<term>'])
        results = bf._api.search.query(terms)
        if len(results) == 0:
            print "No Results."
        else:
            for r in results:
                print " * {}".format(r)

    elif args['create']:
        if args['collection']:
            dest = args['<destination>']
            name = args['<name>']
            c = Collection(name)
            parent = bf.get(dest)
            parent.add(c)
            print c
        elif args['dataset']:
            name = args['<name>']
            ds = bf.create_dataset(name)
            print ds
        else:
            print "Error: creation for object not supported."
            return

    elif args['delete']:
        item = bf.get(args['<item>']) 
        if isinstance(item, Dataset):
            print "Error: cannot delete dataset"
            return
        elif not isinstance(item, BaseNode):
            print "Error: cannot delete item"
            return
        bf.delete(item)

    elif args['upload']:
        files = args['<file>']
        dest  = args['<destination>']
        recursively_upload(bf,dest,files)

    elif args['append']:
        files = args['<file>']
        dest  = args['<destination>']
        bf._api.io.upload_files(dest, files, append=True, display_progress=True)

    elif args['datasets']:
        print "Datasets: "
        for ds in bf.datasets():
            print " - {} (id: {})".format(ds.name, ds.id)

    elif args['dataset']:
        ds = bf.get(args['<dataset>'])
        if args['collaborators']:
            if args['<action>'] == 'ls':
                resp = ds.collaborators()
                print " - Users"
                for u in resp['users']:
                    print "   - email:{} id:{}".format(u.email, u.id)
                print " - Groups"
                for g in resp['groups']:
                    print "   - name:{} id:{}".format(g.name, g.id)
            elif args['<action>'] == 'add':
                ids = args['<action-args>']
                if len(ids) == 0:
                    print "Error: No ids specified"
                    sys.exit(1)
                resp = ds.add_collaborators(*ids)
                print_collaborator_edit_resp(resp)
            elif args['<action>'] == 'rm':
                ids = args['<action-args>']
                if len(ids) == 0:
                    print "Error: No ids specified"
                    sys.exit(1)
                resp = ds.remove_collaborators(*ids)
                print_collaborator_edit_resp(resp)
            else:
                print "Error: invalid dataset collaborators command. Valid commands are 'ls', 'add' or 'rm'"
        else:
            print "Error: invalid dataset command. Valid commands are 'collaborators'"

    elif args['env']:
        print "# Blackfynn environment"
        print "API Location:  {}".format(host)
        print "Streaming API: {}".format(settings.streaming_api_host)
        print "User:          {}".format(email)
        print "Organization:  {} (id: {})".format(bf.context.name, bf.context.id)    

def print_collaborator_edit_resp(resp):
    for key, value in resp.iteritems():
        if value['success']:
            print " - {}: Success".format(key)
        else:
            print " - {}: Error - {}".format(key, value['message'])


def recursively_upload(bf,dest,files):
    dirs = [f for f in files if os.path.isdir(f)]
    files = [f for f in files if os.path.isfile(f)]
    if len(files) > 0:
        bf._api.io.upload_files(dest, files, display_progress=True)
    for d in dirs:
        name = os.path.basename(os.path.normpath(d))
        print 'Uploading to {}'.format(name)
        c = Collection(name)
        parent = bf.get(dest)
        parent.add(c)
        files = [os.path.join(d,f) for f in os.listdir(d) if not f.startswith('.')]
        recursively_upload(bf,c.id,files)
