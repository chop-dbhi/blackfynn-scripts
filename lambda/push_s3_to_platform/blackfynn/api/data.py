# -*- coding: utf-8 -*-
import pandas as pd

import pandas as pd
import pdb
from blackfynn.api.base import APIBase
from blackfynn.models import (
    File, 
    Collection,
    Dataset,
    Organization,
    Tabular,
    TabularSchema,
    TabularSchemaColumn,
    User,
    LedgerEntry
)
import datetime
import math

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Dataset
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DatasetsAPI(APIBase):
    """
    Interface for managing datasets on the platform.
    """
    base_uri='/datasets'
    name = 'datasets'

    def get(self, ds):
        id = self._get_id(ds)
        resp = self._get( self._uri('/{id}', id=id))
        return Dataset.from_dict(resp, api=self.session)

    def get_by_name_or_id(self, name_or_id):
        """
        Get Dataset by name or ID. 

        When using name, this gnores case, spaces, hyphens, and underscores
        such that these are equivelent: 

          - "My Dataset"
          - "My-dataset"
          - "mydataset"
          - "my_DataSet"
          - "mYdata SET"

        """
        def name_key(n):
            return n.lower().strip().replace(' ', '').replace('_','').replace('-','')

        search_key = name_key(name_or_id)

        def is_match(ds):
            return (name_key(ds.name) == search_key) or (ds.id == name_or_id)

        matches = filter(is_match, self.get_all())
        return matches[0] if matches else None

    def get_all(self):
        resp = self._get( self._uri('/'))
        return map(lambda ds: Dataset.from_dict(ds, api=self.session), resp)

    def create(self, ds):
        """
        Create a dataset on the platform
        """
        resp = self._post('', data=ds.as_dict())
        return Dataset.from_dict(resp, api=self.session)

    def update(self, ds):
        """
        Update a dataset on the platform
        """
        id = self._get_id(ds)
        resp = self._put( self._uri('/{id}', id=id), data=ds.as_dict())
        return Dataset.from_dict(resp, api=self.session)

    def get_collaborators(self, ds):
        """
        Get the collaborators for the given data set as a dictionary with users under the 'users' key
        and groups under the 'groups' key
        """
        id = self._get_id(ds)
        resp = self._get(self._uri('/{id}/collaborators', id=id))
        users = map(lambda u: User.from_dict(u, api=self.session), resp['users'])
        groups = map(lambda o: Organization.from_dict(o, api=self.session, object_key=''), resp['groups'])
        return {
            'users': users,
            'groups': groups
        }

    def add_collaborators(self, ds, *collaborator_ids):
        """
        Add the list of user/group ids to this data sets collaborators
        Returns a dictionary of id -> {success: Bool, message: String}. Message will only be set
        if success is False.
        """
        id = self._get_id(ds)
        uri = self._uri('/{id}/collaborators', id=id)
        resp = self._put(uri, data=collaborator_ids)
        return resp

    def remove_collaborators(self, ds, *collaborator_ids):
        """
        Remove the list of user/group ids from this data sets collaborators
        Returns a dictionary of id -> {success: Bool, message: String}. Message will only be set
        if success is False.
        """
        id = self._get_id(ds)
        uri = self._uri('/{id}/collaborators', id=id)
        resp = self._del(uri, data=collaborator_ids)
        return resp


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Collections
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CollectionsAPI(APIBase):
    """
    Interface for managing collections on the platform.
    """
    base_uri='/collections'
    name = 'collections'

    def get(self, coll):
        """
        Return a collection from the platform.

        coll: can be collection object (with id) or string ID
        """
        id = self._get_id(coll)
        resp = self._get( self._uri('/{id}', id=id) )
        return Collection.from_dict(resp, api=self.session)

    def create(self, coll):
        """
        Create a collection on the platform.
        """
        resp = self._post('', data=coll.as_dict())

        # TODO: create children objects??
        return Collection.from_dict(resp, api=self.session)

    def update(self, coll):
        """
        Update a collection on the platform.
        """
        resp = self._put('', data=coll.as_dict())

        # TODO: create children objects??
        return Collection.from_dict(resp, api=self.session)

    def remove_items(self, *items):
        """
        Remove all items from collection
        """
        # remove items (via API) and locally
        r = self.session.data.delete(*items)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DataAPI(APIBase):
    """
    Interface for lower-level data operations on the platform.
    """
    base_uri='/data'
    name = 'data'

    def update_properties(self, thing):
        """
        Update properties for an object/package on the platform.
        """
        path = self._uri('/{id}/properties', id=thing.id)
        body = {"properties": [m.as_dict() for m in thing.properties]}

        return self._put(path, data=body)

    def delete(self, *things):
        """
        Deletes objects from the platform
        """
        ids = list(set([self._get_id(x) for x in things]))
        r = self._post('/delete', data=dict(things=ids))
        if len(r['success']) != len(ids):
            raise Exception("Unable to delete all objects.")

        for thing in things:
            # remove item from local registry
            self.session.core.rm_local(thing.id)
            thing.id = None

        return r

    def move(self, destination, *things):
        """
        Moves objects to the destination package
        """
        ids = [self._get_id(x) for x in things]
        return self._post("/move", data=dict(things=ids, destination=destination))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Packages
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PackagesAPI(APIBase):
    """
    Interface for task/workflow objects on Blackfynn platform
    """
    base_uri = '/packages'
    name = 'packages'

    def create(self, pkg):
        """
        Create data package on platform
        """
        resp = self._post('', data=pkg.as_dict())
        pkg = self._get_package_from_data(resp)
        return pkg

    def update(self, pkg):
        """
        Update package on platform
        """
        resp = self._put(self._uri('/{id}',id=pkg.id), data=pkg.as_dict())
        pkg = self._get_package_from_data(resp)
        return pkg

    def get(self, pkg, include=None):
        """
        Get package object

        pkg:     can be DataPackage ID or DataPackage object.
        include: list of fields to force-include in response (if available)
        """
        pkg_id = self._get_id(pkg)

        params = None
        if include is not None:
            if isinstance(include, basestring):
                params = {'include': include}
            if hasattr(include, '__iter__'):
                params = {'include': ','.join(include)}

        resp = self._get(self._uri('/{id}',id=pkg_id), params=params)

        # TODO: cast to specific DataPackages based on `type`
        pkg = self._get_package_from_data(resp)
        return pkg

    def get_sources(self, pkg):
        """
        Returns the sources of a DataPackage. Sources are the raw, unmodified
        files (if they exist) that contains the package's data.
        """
        pkg_id = self._get_id(pkg)
        resp = self._get(self._uri('/{id}/sources', id=pkg_id))
        for r in resp:
            r['content'].update(dict(pkg_id=pkg_id))

        return [File.from_dict(r, api=self.session) for r in resp]

    def set_sources(self, pkg, *files, **kwargs):
        """
        Sets the sources of a DataPackage. Sources are the raw, unmodified
        files (if they exist) that contains the package's data.
        """
        pkg_id = self._get_id(pkg)
        data = [x.as_dict() for x in files]
        path = self._uri('/{id}/sources', id=pkg_id)
        # Note: PUT returns list of IDs
        resp = self._put(path, data=data, params=kwargs)
        
        return [File.from_dict(r, api=self.session) for r in resp if not isinstance(r, basestring)]

    def get_files(self, pkg):
        """
        Returns the files of a DataPackage. Files are the possibly modified 
        source files (e.g. converted to a different format), but they could also
        be the source files themselves.
        """
        pkg_id = self._get_id(pkg)
        resp = self._get(self._uri('/{id}/files', id=pkg_id))
        for r in resp:
            r['content'].update(dict(pkg_id=pkg_id))

        return [File.from_dict(r, api=self.session) for r in resp]

    def set_files(self, pkg, *files, **kwargs):
        """
        Sets the files of a DataPackage. Files are typically modified 
        source files (e.g. converted to a different format).
        """
        pkg_id = self._get_id(pkg)
        data = [x.as_dict() for x in files]
        path = self._uri('/{id}/files', id=pkg_id)
        resp = self._put(path, data=data, params=kwargs)
        
        return [File.from_dict(r, api=self.session) for r in resp if not isinstance(r, basestring)]

    def get_view(self, pkg):
        """
        Returns the object(s) used to view the package. This is typically a set of
        file objects, that may be the DataPackage's sources or files, but could also be
        a unique object specific for the viewer.
        """
        pkg_id = self._get_id(pkg)
        resp = self._get(self._uri('/{id}/view', id=pkg_id))
        for r in resp:
            r['content'].update(dict(pkg_id=pkg_id))

        return [File.from_dict(r, api=self.session) for r in resp]

    def set_view(self, pkg, *files, **kwargs):
        """
        Set the object(s) used to view the package, if not the file(s) or source(s).
        """
        pkg_id = self._get_id(pkg)
        data = [x.as_dict() for x in files]
        path = self._uri('/{id}/view', id=pkg_id) 
        resp = self._put(path, data=data, params=kwargs)
        
        return [File.from_dict(r, api=self.session) for r in resp if not isinstance(r, basestring)]

    def get_presigned_url_for_file(self, pkg, file):
        args = dict(
            pkg_id = self._get_id(pkg),
            file_id = self._get_id(file)
        )
        resp = self._get(self._uri('/{pkg_id}/files/{file_id}', **args))
        if 'url' in resp:
            return resp['url']
        else:
            raise Exception("Unable to get URL for file ID = {}".format(file_id))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Tabular
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TabularAPI(APIBase):
    base_uri = "/tabular"
    name = 'tabular'

    def _get_data_chunked(self, package, chunk_size, offset, order_by, order_direction):
        path = self._uri('/{id}', id=self._get_id(package))

        params = dict(limit = chunk_size, offset = offset, order_direction = order_direction)
        if order_by is not None:
            params['orderBy'] = order_by

        return self._get(path, params=params)

    def get_tabular_data_iter(self, package, offset, order_by, order_direction, chunk_size=10000):
        """
        Return iterator that yields chunk_size data each call
        """

        if chunk_size > 10000:
            raise ValueError('Chunk size must be less than 10000')

        schema = self.get_table_schema(package)
        column_names = {x.name: x.display_name if x.display_name else x.name
                         for x in schema.column_schema}
        internal_columns = [x.name for x in schema.column_schema if x.internal]

        while True:
            resp = self._get_data_chunked(package, chunk_size=chunk_size, offset=offset, order_direction=order_direction, order_by=order_by)
            offset = offset + chunk_size

            df = pd.DataFrame.from_records(resp['rows'], exclude=internal_columns)
            df.columns = [column_names.get(c) for c in df.columns]

            yield df

            if len(df) < chunk_size:
                break

    def get_tabular_data(self, package, limit, offset, order_by, order_direction):
        """
        Get data for tabular package using iterator
        """
        tab_iter = self.get_tabular_data_iter(package=package, offset=offset, order_by=order_by, order_direction=order_direction)
        df = pd.DataFrame()
        for tmp_df in tab_iter:
            df = df.append(tmp_df)
        return df[0:limit]

    def set_table_schema(self, package, tabular_schema):
        """
        Add a table schema to a tabular package.

        tabular_schema: blackfynn.tabular.models.TabularSchema
        """
        id = self._get_id(package)
        path = self._uri('/{id}/schema', id=id)
        if isinstance(tabular_schema,TabularSchema):
            body = { 'schema' : tabular_schema.as_dict()}
        else:
            body = { 'schema': tabular_schema}

        resp = self._post(path, data=body)
        data = {}
        data['content'] = resp

        return TabularSchema.from_dict(data)

    def get_table_schema(self, package):
        id = self._get_id(package)
        path = self._uri('/{id}/schema', id=id)
        resp = self._get(path)
        return TabularSchema.from_dict(resp)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Files
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class FilesAPI(APIBase):
    """
    Interface for managing file object in Blackfynn
    """
    base_uri = "/files"
    name = 'files'
    
    def create(self, file, destination=None):
        """
        Creates a file under the given destination or its current parent
        """
        container = file.parent if destination is None else destination

        body = file.as_dict()
        body["container"] = container

        response = self._post('', data=body)

        return File.from_dict(response, api=self.session)

    def update(self, file):
        """
        Update a file on the platform
        """
        loc = self._uri('/{id}', id=file.id)
        return self._put(loc, data=file.as_dict())

    def url(self, file):
        """
        Get pre-signed URL for File object
        """
        loc = self._uri('/{id}', id=file.id)
        return self._get(loc)['url']
