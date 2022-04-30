import datetime
from typing import Union, _UnionGenericAlias, Dict, Callable, Type, Any, List, Generic, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic.fields import SHAPE_LIST, SHAPE_GENERIC
from pydantic.generics import GenericModel

parsers: Dict[Type[Any], Callable[[Any], Any]] = {
    datetime.datetime: lambda datetime_string: datetime.datetime.fromisoformat(datetime_string),
    datetime.date: lambda date_string: datetime.date.fromisoformat(date_string),
    datetime.time: lambda time_string: datetime.time.fromisoformat(time_string)
}


class BaseModel(PydanticBaseModel):
    @classmethod
    def construct(cls, _fields_set=None, *, __recursive__=True, **values):
        if not __recursive__:
            return super().construct(_fields_set, **values)

        m = cls.__new__(cls)

        fields_values = {}
        for name, field in cls.__fields__.items():
            if name in values:
                # Field is Union
                if isinstance(field.outer_type_, _UnionGenericAlias):
                    # Iterate over inner types
                    for sub_field in field.sub_fields:
                        # Inner type is Model
                        if issubclass(sub_field.type_, PydanticBaseModel):
                            try:
                                # Construct model out of value
                                fields_values[name] = sub_field.outer_type_.construct(**values[name], __recursive__=True)
                                break
                            except TypeError:
                                continue
                        # Inner type isn't a Model
                        else:
                            fields_values[name] = sub_field.outer_type_(values[name])
                            break
                # Field is List
                elif field.shape == SHAPE_LIST:
                    # List of union
                    if isinstance(field.type_, _UnionGenericAlias):
                        fields_values[name] = []
                        # For each element in the list
                        for element in values[name]:
                            # For each subtype in union
                            for sub_field in field.sub_fields[0].sub_fields:
                                # If subtype is Model
                                if issubclass(sub_field.type_, PydanticBaseModel):
                                    try:
                                        fields_values[name].append(sub_field.outer_type_.construct(**element,
                                                                                                   __recursive__=True))
                                        break
                                    except TypeError:
                                        continue
                                else:
                                    fields_values[name].append(element)
                                    break
                                    # fields_values[name] = sub_field.outer_type_(**values[name])
                    # List of models
                    elif issubclass(field.type_, PydanticBaseModel):
                        fields_values[name] = [field.type_.construct(**element) for element in values[name]]
                    # Just a list
                    else:
                        try:
                            fields_values[name] = [parsers[field.type_](**element) for element in values[name]]
                        except (ValueError, KeyError):
                            fields_values[name] = values[name]
                # Field is Model
                elif field.shape == SHAPE_GENERIC:
                    pass
                elif issubclass(field.type_, PydanticBaseModel):
                    fields_values[name] = field.outer_type_.construct(**values[name], __recursive__=True)
                # Field is simple value
                else:
                    try:
                        fields_values[name] = parsers[field.type_](values[name])
                    except (ValueError, KeyError) as ex:
                        fields_values[name] = values[name]

            elif not field.required:
                fields_values[name] = field.get_default()

        object.__setattr__(m, '__dict__', fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        object.__setattr__(m, '__fields_set__', _fields_set)
        m._init_private_attributes()
        return m


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

    class Model(GenericModel, Generic[DataType]):
        data: DataType

    class Complex(BaseModel):
        model: Model[Base]

    _complex = Complex.construct(model={'data': {'number': 1}})

    assert _complex.model.data.number == 'Hello World'


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
