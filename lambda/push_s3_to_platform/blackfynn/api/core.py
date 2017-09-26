# -*- coding: utf-8 -*-
from blackfynn.api.base import APIBase
from blackfynn.models import (
    BaseCollection,
    DataPackage,
    Dataset,
    Organization,
    User,
    get_package_class
)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Core API
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CoreAPI(APIBase):
    """
    Special higher-level API actions that may use other registered APIs.
    All in the name of convenience. 
    """
    name = 'core'

    def __init__(self, *args, **kwargs):
        super(CoreAPI, self).__init__(*args, **kwargs)
        self._data_registry = {}

    def create(self, thing):
        """
        Create an object on the platform. This will create the
        object and all sub-objects (if they do not exist).
        """
        if thing.exists:
            thing._api = self.session
            return thing

        if (not isinstance(thing, Dataset)) and (thing.parent is None):
            raise Exception("Object not created. Must have a parent/destination.")

        if isinstance(thing, DataPackage):
            item = self.session.packages.create(thing)
        elif isinstance(thing, Dataset):
            item = self.session.datasets.create(thing)
        elif isinstance(thing, BaseCollection):
            item = self.session.collections.create(thing)
        else:
            raise Exception('Unable to create object.')

        item._api = self.session

        self.set_local(item)
        return item

    def update(self, thing):
        """
        Updates an object onthe platform. This will update all
        sub-objects as well, if available.
        """

        if isinstance(thing, DataPackage):
            item = self.session.packages.update(thing)
        elif isinstance(thing, Dataset):
            item = self.session.datasets.update(thing)
        elif isinstance(thing, BaseCollection):
            item = self.session.collections.update(thing)
        else:
            raise Exception('Unable to update object.')
        
        self.set_local(item)
        return item

    def get(self, thing, update=True):
        """
        Get any object from id. Assumes the below APIs are registered
        with the session.
        """
        local_thing = self.get_local(thing)
        if (local_thing is not None) and (not update):
            return local_thing

        id = self._get_id(thing)

        if ':package:' in id:
            item = self.session.packages.get(id)
        elif ':collection:' in id:
            item = self.session.collections.get(id)
        elif ':dataset:' in id:
            item = self.session.datasets.get(id)
        else:
            raise Exception('Unknown object.')

        self.set_local(item)
        return item

    def delete(self, *things):
        """
        Deletes objects from the platform. Assumes Data API is registered.
        """
        self.session.data.delete(*things)
        for thing in things:
            if hasattr(thing, 'parent'):
                # attempt to remove from parent object
                p = self.get_local(thing.parent)
                p._items = None
                thing.parent = None
            thing.id = None

    def set_local(self, thing):
        self._data_registry.update({thing.id:thing})

    def get_local(self, thing):
        id = self._get_id(thing)
        return self._data_registry.get(id, None)

    def get_locals(self):
        return self._data_registry.values()

    def rm_local(self, thing):
        id = self._get_id(thing)
        return self._data_registry.pop(id, None)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Organizations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class OrganizationsAPI(APIBase):
    """
    Interface for task/workflow objects on Blackfynn platform
    """
    base_uri = '/organizations'
    name = 'organizations'

    def get_all(self):
        """
        Get all organizations for logged-in user.
        """
        my_orgs = self._get('?includeAdmins=false')['organizations']

        return [Organization.from_dict(x, api=self.session) for x in my_orgs]

    def get(self, org=None):
        """
        Get an organization.

        org: Organization class or id string
        """
        id = self._get_id(org)
        resp = self._get(self._uri('/{id}', id=id))
        return Organization.from_dict(resp, api=self.session)

    def get_teams(self, org):
        id = self._get_id(org)
        return self._get(self._uri('{id}/teams', id=org))

    def get_members(self, org):
        id = self._get_id(org)
        return self._get(self._uri('{id}/members', id=org))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Security
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SecurityAPI(APIBase):
    """
    Interface for interacting with Blackfynn's security model
    """
    base_uri = '/security'
    name = 'security'

    permissions = set([
            "READ",
            "WRITE",
            "ANNOTATE",
            "DOWNLOAD",
            "DELETE",
            "ADMINISTER"
        ])

    def grant_permissions(self, object_id, user_id, permission):
        """
        body = {
          "itemId": "string",
          "principalId": "string",
          "permission": "string"
        }
        """
        permission = permission.upper()
        assert permission in self.permissions, "Unacceptable permission"

        body = {
            "itemId": object_id,
            "principalId": user_id,
            "permission": permission,
        }

        self._post('/permissions', data=body)

    def get_upload_credentials(self, group_id, destination_id):
        """
        Get temporary credentials for a users folder in the s3 bucket
        """
        return self._get(
                self._uri(
                    '/user/credentials/upload/{group_id}/{dest_id}',
                    group_id=group_id,
                    dest_id=destination_id))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Search
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SearchAPI(APIBase):
    """
    Interface for searching Blackfynn
    """
    base_uri = '/search'
    name = 'search'

    def query(self, terms, max_results=10):
        data = dict(
            query = terms,
            maxResults = max_results
        )
        resp = self._post(endpoint='', data=data) 

        results = []
        for r in resp:
            pkg_cls = get_package_class(r)
            pkg = pkg_cls.from_dict(r, api=self.session)
            results.append(pkg)

        return results
