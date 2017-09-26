import pytest
import pdb
from blackfynn import TimeSeries, TimeSeriesChannel
from blackfynn.models import TimeSeriesAnnotationLayer, TimeSeriesAnnotation
from blackfynn.models import Tabular, TabularSchema, TabularSchemaColumn


def test_search(client, dataset):
    # create
    ts = TimeSeries('Human EEG')
    assert not ts.exists
    dataset.add(ts)
    assert ts.exists
    assert ts in dataset
    assert ts.type == 'TimeSeries'
    assert ts.name == 'Human EEG'
    ts2 = client.get(ts.id)
    assert ts2.id == ts.id
    assert ts2.name == ts.name
    assert ts2.type == 'TimeSeries'
    del ts2

    t = Tabular('Some tabular data')
    assert not t.exists
    assert t.schema is None

    # create
    dataset.add(t)
    assert t.exists
    assert t.schema is None

    schema = [
        TabularSchemaColumn(
            name = '',
            display_name = 'index',
            datatype = 'Integer',
            primary_key = True,
            internal = True
        ),
        TabularSchemaColumn(
            name = '',
            display_name = 'email',
            datatype = 'String',
            primary_key = False,
            internal = False
        ),
    ]

    s = TabularSchema(name="schema", column_schema=schema)

    t.set_schema(s)
    assert t.name == 'Some tabular data'
    assert t.exists
    a = t.get_schema()
    assert a.exists

    a = client.search('email')
