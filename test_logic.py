from mylib.logic import hello_world,hello_nik


def test_hello_world():
    assert hello_world() == "Hello, world!"
    
def test_hello_nik():
    name = 'Nik'
    assert hello_nik(name) == "Hello, Nik!"