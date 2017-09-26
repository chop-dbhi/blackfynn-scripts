# -*- coding: utf-8 -*-

import requests

# blackfynn-specific
from blackfynn import settings
from blackfynn.models import Dataset
from blackfynn.api.transfers import IOAPI
from blackfynn.api.compute import ComputeAPI
from blackfynn.api.ledger import LedgerAPI
from blackfynn.api.timeseries import TimeSeriesAPI
from blackfynn.base import ClientSession
from blackfynn.api.core import (
    CoreAPI, SecurityAPI, OrganizationsAPI, SearchAPI
)
from blackfynn.api.data import (
    DatasetsAPI, CollectionsAPI, PackagesAPI, FilesAPI, DataAPI, TabularAPI
)


class Blackfynn(object):
    """
    The client provides an interface to the Blackfynn platform, giving you the
    ability to retrieve, add, and manipulate data.

    Args:
        email (str, optional): User's email address
        password (str, optional): User's password
        host (str, optional): API address
        streaming_host (str, optional): Streaming API address

    Examples:
        Load the client library and initialize::

            from blackfynn import Blackfynn

            # note: no user/password needed if environment variables are set
            bf = Blackfynn()

        Retrieve/modify items on the platform::

            # get some dataset
            ds = bf.get_dataset('my dataset')
            print "Dataset {} has ID={}".format(ds.name, ds.id)

            # list all first-level items in dataset
            for item in ds:
                print "Item: {}".format(item)

            # grab some data package
            pkg = bf.get("N:package:1234-1234-1234-1234")

            # modify a package's name
            pkg.name = "New Package Name"

            # add some property
            pkg.insert_property('Author', 'Mork Horlenbork')

            # sync changes
            pkg.update()


    Note:
        To initialize your ``Blackfynn`` client without passing any arguments, ensure that you
        have your environment variables set properly:

            - ``BLACKFYNN_USER``
            - ``BLACKFYNN_PASS``

    """
    def __init__(self, email=None, password=None, host=None, streaming_host=None):
        if email is None:
            if settings.api_user is None:
                raise Exception("Error: no email/user found. Cannot connect.")
            email = settings.api_user

        if password is None:
            if settings.api_pass is None:
                raise Exception("Error: no password found. Cannot connect.")
            password = settings.api_pass

        if host is None:
            host = settings.api_host

        if streaming_host is None:
            streaming_host = settings.streaming_api_host

        self.host = host
        self.streaming_host = streaming_host

        # direct interface to REST API.
        self._api = ClientSession(user=email, password=password, host=host, streaming_host=streaming_host)

        # account
        try:
            self._api.login()
        except Exception as e:
            print e
            raise Exception("Unable to login using specified user/password.")

        self._api.register(
            CoreAPI,
            OrganizationsAPI,
            DatasetsAPI,
            CollectionsAPI,
            FilesAPI,
            DataAPI,
            PackagesAPI,
            TimeSeriesAPI,
            TabularAPI,
            SecurityAPI,
            ComputeAPI,
            SearchAPI,
            IOAPI,
            LedgerAPI
        )

        # set default organization if only one present
        orgs = self.organizations()
        if len(orgs) >= 1:
            self._api._context = orgs[0]
            self._api._session.headers.update({'X-ORGANIZATION-ID': self._api._context.id})

    def set_context(self, org):
        """
        Explicitly set the organizational context for future operations.

        Args:
            org (Organization or str): An organization ID or object

        Example::

            # log in
            bf = Blackfynn()

            # set organizational context
            bf.set_context('My Organization')
            # datasets for "My Organization"
            print client.datasets()

            # set organizational context, again
            bf.set_context('My Other Organization')
            # datasets for "My Other Organization"
            print client.datasets()

        """
        orgs_by_name = filter(lambda x: x.name.strip().lower()==org.strip().lower(), self.organizations())
        orgs_by_id   = filter(lambda x: x.id.strip()==org.strip(), self.organizations())

        orgs = orgs_by_name + orgs_by_id
        if not orgs:
            raise Exception('Unable to set context. Organization "{org}" not found.'.format(org=org))

        self._api._context = orgs[0]
        self._api._session.headers.update({'X-ORGANIZATION-ID': self._api._context.id})

    @property
    def context(self):
        """
        The current organizational context of the active client.
        """
        return self._api._context

    @property
    def profile(self):
        """
        The profile of the current active user.
        """
        return self._api.profile

    def organizations(self):
        """
        Return all organizations for user.
        """
        return self._api.organizations.get_all()

    def datasets(self):
        """
        Return all datasets for user for an organization (current context).
        """
        self._check_context()
        return self.context.datasets

    def get(self, id, update=True):
        """
        Get any object by ID. 

        Args:
            id (str): The ID of the Blackfynn object.

        Returns:
            Object of type/subtype ``DataPackage``, ``Collection``, or ``Dataset``.
        """
        return self._api.core.get(id, update=update)

    def upload(self, destination, *files):
        """
        Upload file(s) to the platform.

        Args:
            destination (object or str): Destination ID or object. 
                Supported destinations are``Dataset`` or ``Collection``.
            files (list): one or more files to be uploaded.

        Examples:
            You can upload a single file::

                bf.upload(my_dataset, '/path/to/some/data.nii.gz')

            Or you can upload multiple things that will be processed simultaneously::

                bf.upload(my_collection, '/path/to/one_thing.svs', '/path/to/another.pdf')

        Note:
            Uploads invoked together correspond to the same upload "group", in which
            any files that could be grouped together (some data formats rely on multiple files)
            will be grouped together, if possible. For example, the Analyze MRI format contains
            both a ``.hdr`` and ``.img`` file. These should always be uploaded together::

                bf.upload(my_dest, '/some/brain.hdr', '/some/brain.img')
            
            Note that these *can* be uploaded together with other, unrelated, file(s) as well.::

                bf.upload(my_dest, '/some/brain.hdr', '/some/brain.img', '/some/other/notes.pdf')

        """
        return self._api.io.upload_files(destination, files)

    def create_dataset(self, name):
        """
        Create a dataset under the active organization.

        Args:
            name (str): The name of the to-be-created dataset

        Returns:
            The created ``Dataset`` object

        """
        self._check_context()
        return self._api.core.create(Dataset(name))

    def get_dataset(self, name_or_id):
        """
        Get Dataset by name or ID. 

        Args:
            name_or_id (str): the name or the ID of the dataset

        Note:
            When using name, this method gnores case, spaces, hyphens, 
            and underscores such that these are equivelent: 

              - "My Dataset"
              - "My-dataset"
              - "mydataset"
              - "my_DataSet"
              - "mYdata SET"

        """
        result = self._api.datasets.get_by_name_or_id(name_or_id)
        if result is None:
            raise Exception("No dataset matching name or ID '{}'.".format(name_or_id))
        return result

    def update(self, thing):
        """
        Update an item on the platform.

        Args:
            thing (object or str): the ID or object to update

        Example::

            my_eeg = bf.get('N:package:1234-1234-1234-1234')
            my_eeg.name = "New EEG Name"
            bf.update(my_eeg)

        Note:
            You can also call update directly on objects, for example::

                my_eeg.name = "New EEG Name"
                my_eeg.update()

        """ 
        return self._api.core.update(thing)

    def delete(self, *things):
        """
        Deletes items from the platform.

        Args:
            things (list): ID or object of items to delete

        Example::

            # delete a package by passing in object
            bf.delete(my_package)

            # delete a package by ID
            bf.delete('N:package:1234-1234-1234-1235')

            # delete many things (mix of IDs and objects)
            bf.delete(my_package, 'N:collection:1234-1234-1234-1235', another_collection)

        Note:
            When deleting ``Collection``, all child items will also be deleted.

        """
        return self._api.core.delete(*things)

    def move(self, destination, *things):
        """
        Moves item(s) from their current location to the destination.

        Args:
            destination (object or str): The ID of the destination. This must be of type
                type ``Collection`` or ``Dataset``.
            things (list): the IDs or objects to move.

        """
        r = self._api.data.move(destination, *things)

    def search(self, query, max_results=10):
        """
        Find an object on the platform. 

        Args:
            query (str): query string to perform search.
            max_results (int, optional): the number of results to return

        Example::

            # find some items belonging to patient123
            for result in  bf.search('patient123'):
                print "found:", result

        """
        return self._api.search.query(query, max_results=max_results)
        
    def _check_context(self):
        if self.context is None:
            raise Exception('Must set context before executing method.') 

    def __repr__(self):
        return "<Blackfynn user='{}' organization='{}'>".format(self.profile.email, self.context.name)
