import datetime
from typing import Union, List, Generic, TypeVar, Optional, Any

from pydantic.generics import GenericModel

from model import BaseModel


def test_validity():
    # TODO: Make model much more complex
    class Model(BaseModel):
        number: int
        text: str

    class Complex(BaseModel):
        model: Model

    data = {
        'model': {
            'number': 5,
            'text': 'Hello World'
        }
    }

    assert Complex(**data) == Complex.construct(**data)


# Doesn't actually test anything but can give some info about performance
def test_performance():
    import timeit
    from functools import partial

    class Model(BaseModel):
        number: int
        text: str

    class Complex(BaseModel):
        model: Model

    def construct(values):
        return Complex.construct(**values)

    def normal(values):
        return Complex(**values)

    data = {
        'model': {
            'number': 5,
            'text': 'Hello World'
        }
    }

    print(timeit.timeit(partial(construct, values=data), number=100))
    print(timeit.timeit(partial(normal, values=data), number=100))


def test_simple_model():
    class Model(BaseModel):
        number: int

    model = Model.construct(number=5)

    assert model.number == 5


def test_field_types():
    class Model(BaseModel):
        time: datetime.time
        date: datetime.date
        datetime: datetime.datetime

    now = datetime.datetime.now()

    model = Model.construct(time=now.time().strftime('%H:%M:%S.%f'),
                            date=now.date().strftime('%Y-%m-%d'),
                            datetime=now.strftime('%Y-%m-%dT%H:%M:%S.%f%z'))

    assert model.time == now.time()
    assert model.date == now.date()
    assert model.datetime == now


def test_complex_model():
    class Model(BaseModel):
        number: int
        text: str

    class Complex(BaseModel):
        model: Model

    _complex = Complex.construct(model={'number': 5, 'text': 'Hello World'})

    assert isinstance(_complex.model, Model)
    assert _complex.model.number == 5
    assert _complex.model.text == 'Hello World'


def test_union():
    class Model(BaseModel):
        # Union order is super critical, since an int can be a string,
        # but not vice-versa the most specific type should be first
        attribute: Union[int, str]

    model = Model.construct(attribute=5)

    assert model.attribute == 5


def test_complex_union():
    class Model(BaseModel):
        number: int

    class Complex(BaseModel):
        attribute: Union[Model, str]

    _complex = Complex.construct(attribute='Test')

    assert isinstance(_complex.attribute, str)
    assert _complex.attribute == 'Test'

    _complex = Complex.construct(attribute={'number': 5})

    assert isinstance(_complex.attribute, Model)
    assert _complex.attribute.number == 5


def test_simple_list():
    class Model(BaseModel):
        lst: List[str]

    model = Model.construct(lst=['a', 'a', 'a'])

    assert isinstance(model.lst, list)
    assert len(model.lst) == 3
    assert model.lst == ['a', 'a', 'a']


def test_complex_list():
    class Model(BaseModel):
        number: int

    class Complex(BaseModel):
        lst: List[Model]

    _complex = Complex.construct(lst=[{'number': 1}, {'number': 2}])

    assert isinstance(_complex.lst, list)
    assert len(_complex.lst) == 2
    assert all([isinstance(element, Model) for element in _complex.lst])


def test_union_complex_list():
    class Model(BaseModel):
        number: int

    class Complex(BaseModel):
        lst: List[Union[Model, str]]

    _complex = Complex.construct(lst=[{'number': 1}, 'string'])

    assert isinstance(_complex.lst, list)
    assert len(_complex.lst) == 2
    assert isinstance(_complex.lst[0], Model)
    assert isinstance(_complex.lst[1], str)


DataType = TypeVar('DataType')


def test_generic_simple():
    class Model(GenericModel, Generic[DataType]):
        data: DataType

    model = Model[str].construct(data='Hello World')

    assert model.data == 'Hello World'


def test_generic_complex():
    class Model(GenericModel, Generic[DataType]):
        data: DataType

    class Complex(BaseModel):
        model: Model[str]

    _complex = Complex.construct(model={'data': 'something'})

    assert _complex.model.data == 'something'


def test_nested_generic_complex():
    class Base(BaseModel):
        number: int

    class Model(BaseModel, GenericModel, Generic[DataType]):
        data: DataType

    class Complex(BaseModel):
        model: Model[Base]

    _complex = Complex.construct(model={'data': {'number': 1}})

    assert _complex.model.data.number == 1


def test_list_generic():
    class Model(GenericModel, Generic[DataType]):
        data: DataType

    class Complex(BaseModel):
        lst: List[Model[str]]

    _complex = Complex.construct(lst=[{'data': 'Hello World'}, {'data': 'something'}])

    assert isinstance(_complex.lst, list)
    assert len(_complex.lst) == 2
    assert all([isinstance(element, Model) for element in _complex.lst])
    assert _complex.lst[0].data == 'Hello World'


def test_list_complex_generic():
    class Base(BaseModel):
        number: int

    class Model(BaseModel, GenericModel, Generic[DataType]):
        data: DataType

    class Complex(BaseModel):
        lst: List[Model[Base]]

    _complex = Complex.construct(lst=[{'data': {'number': 1}}, {'data': {'number': 2}}])

    assert isinstance(_complex.lst, list)
    assert len(_complex.lst) == 2
    assert all([isinstance(element, Model) for element in _complex.lst])
    assert _complex.lst[0].data.number == 1
    assert _complex.lst[1].data.number == 2
    assert _complex.lst[0].data.dict() == {'number': 1}


def test_special_form_type_any():
    class Model(BaseModel):
        field_any: Any
        field_list_any: List[Any]

    model = Model.construct(field_any=5, field_list_any=[1, 2])

    assert model.field_any == 5
    assert isinstance(model.field_list_any, list)
    assert len(model.field_list_any) == 2
    assert model.field_list_any[0] == 1
    assert model.field_list_any[1] == 2


def test_special_form_type_optional():
    class Model(BaseModel):
        optional: Optional[str]

    model = Model.construct(optional='Hello World')
    empty = Model.construct()

    assert model.optional == 'Hello World'
    assert empty.optional is None
