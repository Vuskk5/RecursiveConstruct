import datetime
from typing import Dict, Type, Any, Callable, _UnionGenericAlias

from pydantic import BaseModel as PydanticBaseModel
from pydantic.fields import SHAPE_LIST, SHAPE_GENERIC


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
                elif field.shape == SHAPE_GENERIC:
                    pass
                # Field is Model
                elif issubclass(field.type_, PydanticBaseModel):
                    temp = field.outer_type_.construct(**values[name], __recursive__=True)
                    fields_values[name] = temp
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


parsers: Dict[Type[Any], Callable[[Any], Any]] = {
    datetime.datetime: lambda datetime_string: datetime.datetime.fromisoformat(datetime_string),
    datetime.date: lambda date_string: datetime.date.fromisoformat(date_string),
    datetime.time: lambda time_string: datetime.time.fromisoformat(time_string)
}