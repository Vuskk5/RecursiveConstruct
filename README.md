# Supported Types

```python
import datetime

from model import BaseModel


class ExampleModel(BaseModel):
    number: int  # Simple variable
    current_time: datetime.date  # Special variable


class ComplexModel(BaseModel):
    instance: ExampleModel  # Recursive model (Attribute is subclass of BaseModel)
    text_lines: list[str]  # List of simple objects
    models: list[ExampleModel]  # List of models
```

# Special Forms
```python
class Model(BaseModel):
    union: Union[ExampleModel, str]
    union_list: list[Union[ExampleModel, str]]
```

# Generics
```python
DataType = TypeVar('DataType')

class TestGeneric(BaseModel, GenericModel, Generic[DataType]):
    data: DataType

class ComplexModel(BaseModel):
    generic_simple: TestGeneric[str]
    generic_complex: TestGeneric[ExampleModel]
    generic_list: list[TestGeneric[str]]
```
For generics, the generic class must also extend `BaseModel` so that it's `construct()` will be inherited.

# Custom parsers

Custom parsers exist for the following types:

```python
import datetime

datetime.time
datetime.date
datetime.datetime
```