import os
import pytest

from blackfynn import Blackfynn

def pytest_addoption(parser):
    parser.addoption("--devserver", default=[], help=("Test against dev server (not local)"))

def pytest_generate_tests(metafunc):
    print metafunc.fixturenames
    use_dev = False
    if 'devserver' in metafunc.fixturenames:
        use_dev = metafunc.config.option.devserver
    metafunc.parametrize("use_dev", [use_dev], scope='session')
    

@pytest.fixture(scope='session')
def client(use_dev):
    """
    Login via API, return client. Login information, by default, will be taken from
    environment variables, so ensure those are set properly before testing. Alternatively,
    to force a particular user, adjust input arguments as necessary.
    """
    bf = Blackfynn()
    # get organizations
    orgs = bf.organizations()
    print 'organizations =', orgs
    assert len(orgs) > 0

    # explicitly set context to Blackfyn org
    bf.set_context('Test Organization')
    assert bf.context is not None
    return bf

@pytest.fixture(scope='session')
def client2(use_dev):
    bf = Blackfynn('test2@blackfynn.com', 'password')
    # get organizations
    orgs = bf.organizations()
    assert len(orgs) > 0

    # explicitly set context to Blackfyn org
    bf.set_context('Test Organization')
    assert bf.context is not None
    return bf


@pytest.fixture(scope='session')
def superuser_client(use_dev):
    """
    Client using super-admin permissions
    """
    bf = Blackfynn('etluser@blackfynn.com', 'password')
    assert bf.profile.is_super_admin
    return bf


@pytest.fixture(scope='session')
def dataset(use_dev, client, superuser_client):
    """
    Test Dataset to be used by other tests.
    """

    # collection of all datasets
    datasets = client.datasets()
    n_ds = len(datasets)

    # create test dataset
    ds = client.create_dataset('My Test Dataset')
    assert ds.exists
    assert len(client.datasets()) == n_ds + 1

    # surface test dataset to other functions
    yield ds

    # update name of dataset
    ds.name = 'Same Dataset, Different Name'
    ds.update()
    ds2 = client.get(ds)
    assert ds2.id == ds.id
    assert ds2.name == ds.name

    # remove
    superuser_client.delete(ds)

    assert len(client.datasets()) == n_ds
    assert not ds.exists
    assert not hasattr(ds, 'parent')

@pytest.fixture(scope='session')
def test_organization(client):
    return filter(lambda o: o.name == 'Test Organization', client.organizations())[0]

def test_login(client):
    email = os.environ.get('BLACKFYNN_USER')
    profile = client.profile
    print "profile = ", profile
    assert profile['email'] == email

