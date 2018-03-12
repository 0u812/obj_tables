import pkg_resources

with open(pkg_resources.resource_filename('obj_model', 'VERSION'), 'r') as file:
    __version__ = file.read().strip()
# :obj:`str`: version

# API
from .core import (Model, Attribute,
                   LiteralAttribute, NumericAttribute, EnumAttribute, BooleanAttribute, FloatAttribute,
                   IntegerAttribute, PositiveIntegerAttribute, StringAttribute, LongStringAttribute,
                   RegexAttribute, SlugAttribute, UrlAttribute, DateAttribute, TimeAttribute,
                   DateTimeAttribute, RelatedAttribute, OneToOneAttribute, OneToManyAttribute,
                   ManyToOneAttribute, ManyToManyAttribute,
                   InvalidObjectSet, InvalidModel, InvalidObject, InvalidAttribute, Validator,
                   ObjModelWarning, SchemaWarning,
                   ModelSource, TabularOrientation,
                   get_models, get_model, excel_col_name)
from . import abstract
from . import extra_attributes
from . import io
from . import utils
