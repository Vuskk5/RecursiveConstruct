# Supported Types

```python
import datetime
from typing import Union

from model import BaseModel


class ExampleModel(BaseModel):
    number: int  # Simple variable
    current_time: datetime.date  # Special variable

    
DataType = TypeVar('DataType')

class TestGeneric(BaseModel, GenericModel, Generic[DataType]):
    data: DataType
    

class ComplexModel(BaseModel):
    instance: ExampleModel  # Recursive model (Attribute is subclass of BaseModel)
    text_lines: list[str]  # List of simple objects
    models: list[ExampleModel]  # List of models
    union: Union[ExampleModel, str]  # Union
    union_list: list[Union[ExampleModel, str]]  # List of union
    generic_simple: TestGeneric[str]    # Generic object
    generic_complex: TestGeneric[ExampleModel]  # Generic Attribute is model
    generic_list: list[TestGeneric[str]]    # List of generic objects
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