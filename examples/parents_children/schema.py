# Schema automatically generated at 2019-09-19 16:49:11

import obj_tables


class Parent(obj_tables.Model):
    id = obj_tables.StringAttribute(unique=True, primary=True, verbose_name='Id')
    name = obj_tables.StringAttribute(verbose_name='Name')

    class Meta(obj_tables.Model.Meta):
        table_format = obj_tables.TableFormat.column
        attribute_order = ('id', 'name',)


class Child(obj_tables.Model):
    id = obj_tables.StringAttribute(unique=True, primary=True, verbose_name='Id')
    name = obj_tables.StringAttribute(verbose_name='Name')
    gender = obj_tables.EnumAttribute(['female', 'male'], verbose_name='Gender')
    parents = obj_tables.ManyToManyAttribute('Parent', related_name='children', verbose_name='Parents')
    favorite_video_game = obj_tables.ManyToOneAttribute('Game', related_name='children', verbose_name='FavoriteVideoGame')

    class Meta(obj_tables.Model.Meta):
        table_format = obj_tables.TableFormat.row
        attribute_order = ('id', 'name', 'gender', 'parents', 'favorite_video_game',)


class Game(obj_tables.Model):
    name = obj_tables.StringAttribute(unique=True, primary=True, verbose_name='Name')
    publisher = obj_tables.StringAttribute(verbose_name='Publisher')
    year = obj_tables.IntegerAttribute(verbose_name='Year')

    class Meta(obj_tables.Model.Meta):
        table_format = obj_tables.TableFormat.multiple_cells
        attribute_order = ('name', 'publisher', 'year',)