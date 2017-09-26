from blackfynn.api.base import APIBase
from blackfynn.models import (
    Dataset, Collection, Tabular,TabularSchemaColumn
)
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

    def find_tabular_column(self,client,target_id,column):
        """
        Find packages with column
        """
        return_pkgs = []
        pkg = client._api.core.get(target_id)
        if isinstance(pkg, Collection) or isinstance(pkg, Dataset):
            #find packages in collection that are tabular
            print 'Searching in {}'.format(pkg.name)
            pkgs = pkg.items
            for i in pkgs:
                return_pkg = self.find_tabular_column(client,i.id,column)
                if return_pkg:
                    return_pkgs.extend(return_pkg)
        elif isinstance(pkg, Tabular):
            schema = pkg.get_schema()
            col_names = [s.display_name for s in schema.column_schema]
            if column in col_names:
                return [pkg]
        return return_pkgs
