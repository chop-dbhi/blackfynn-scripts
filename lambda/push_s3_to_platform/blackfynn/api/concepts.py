# -*- coding: utf-8 -*-

from blackfynn.api.base import APIBase
from blackfynn.models import (
    Concept
)
import pdb

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Concepts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ConceptsAPI(APIBase):
    base_uri = "/concept"
    name = 'concepts'

    def get_all_concepts(self):
        path = self._uri('/')
        resp = self._get(path)
        return [Concept.from_dict(x,api=self.session) for x in resp]

    def get_concept(self,name):
        path = self._uri('/{name}',name=name)
        resp = self._get(path)
        return Concept.from_dict(resp,api=self.session)
