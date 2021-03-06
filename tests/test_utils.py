""" Data model to represent models.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""
import git
import numpy.random
import numpy.testing
import obj_tables
import obj_tables.io
import os
import shutil
import sys
import tempfile
import unittest
import wc_utils.workbook
import wc_utils.workbook.io
from obj_tables import core, utils
from obj_tables.utils import DataRepoMetadata, SchemaRepoMetadata
from wc_utils.util.git import GitHubRepoForTests, RepoMetadataCollectionType
from wc_utils.util.types import get_subclasses


class Root(core.Model):
    id = core.StringAttribute(max_length=1, primary=True, unique=True, verbose_name='Identifier')


class Node(core.Model):
    id = core.StringAttribute(max_length=2, primary=True, unique=True)
    root = core.ManyToOneAttribute(Root, related_name='nodes')


class Leaf(core.Model):
    id = core.StringAttribute(primary=True)
    node = core.ManyToOneAttribute(Node, related_name='leaves')


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.root = Root(id='root')
        self.nodes = [
            Node(root=self.root, id='node-0'),
            Node(root=self.root, id='node-1'),
        ]
        self.leaves = [
            Leaf(node=self.nodes[0], id='leaf-0-0'),
            Leaf(node=self.nodes[0], id='leaf-0-1'),
            Leaf(node=self.nodes[1], id='leaf-1-0'),
            Leaf(node=self.nodes[1], id='leaf-1-1'),
        ]

    def test_get_related_models(self):
        class DisjointParent(core.Model):
            id = core.StringAttribute(primary=True, unique=True)

        class DisjointChild(core.Model):
            parent = core.ManyToOneAttribute(DisjointParent, related_name='children')

        self.assertEqual(set(utils.get_related_models(Root)), set([Node, Leaf]))
        self.assertEqual(set(utils.get_related_models(Node)), set([Root, Leaf]))
        self.assertEqual(set(utils.get_related_models(Leaf)), set([Root, Node]))
        self.assertEqual(set(utils.get_related_models(Root, include_root_model=True)), set([Root, Node, Leaf]))
        self.assertEqual(set(utils.get_related_models(Node, include_root_model=True)), set([Root, Node, Leaf]))
        self.assertEqual(set(utils.get_related_models(Leaf, include_root_model=True)), set([Root, Node, Leaf]))

        self.assertEqual(set(utils.get_related_models(DisjointParent)), set([DisjointChild]))
        self.assertEqual(set(utils.get_related_models(DisjointChild)), set([DisjointParent]))
        self.assertEqual(set(utils.get_related_models(DisjointParent, include_root_model=True)), set([DisjointParent, DisjointChild]))
        self.assertEqual(set(utils.get_related_models(DisjointChild, include_root_model=True)), set([DisjointChild, DisjointParent]))

    def test_get_attribute_by_name(self):
        self.assertEqual(utils.get_attribute_by_name(Root, None, None), (None, None))

        self.assertEqual(utils.get_attribute_by_name(Root, None, 'id'), (None, Root.Meta.attributes['id']))
        self.assertEqual(utils.get_attribute_by_name(Root, None, 'id2'), (None, None))
        self.assertEqual(utils.get_attribute_by_name(Root, None, 'Identifier', verbose_name=True), (None, Root.Meta.attributes['id']))
        self.assertEqual(utils.get_attribute_by_name(Root, None, 'Identifier2', verbose_name=True), (None, None))

        self.assertEqual(utils.get_attribute_by_name(Root, None, 'ID', case_insensitive=True), (None, Root.Meta.attributes['id']))
        self.assertEqual(utils.get_attribute_by_name(Root, None, 'ID', case_insensitive=False), (None, None))
        self.assertEqual(utils.get_attribute_by_name(Root, None, 'identifier', verbose_name=True,
                                                     case_insensitive=True), (None, Root.Meta.attributes['id']))
        self.assertEqual(utils.get_attribute_by_name(Root, None, 'identifier', verbose_name=True, case_insensitive=False), (None, None))

        class Parent(core.Model):
            quantity_1 = core.OneToOneAttribute('Quantity', related_name='parent_q_1')
            quantity_2 = core.OneToOneAttribute('Quantity', related_name='parent_q_2')
            value = core.FloatAttribute()
            units = core.StringAttribute()

            class Meta(core.Model.Meta):
                attribute_order = ('quantity_1', 'quantity_2', 'value', 'units')

        class Quantity(core.Model):
            value = core.FloatAttribute()
            units = core.StringAttribute()

            class Meta(core.Model.Meta):
                attribute_order = ('value', 'units')
                table_format = core.TableFormat.multiple_cells

            def serialize(self):
                return '{} {}'.format(value, units)

        self.assertEqual(utils.get_attribute_by_name(Parent, 'quantity_1', 'value'),
                         (Parent.Meta.attributes['quantity_1'], Quantity.Meta.attributes['value']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'quantity_1', 'units'),
                         (Parent.Meta.attributes['quantity_1'], Quantity.Meta.attributes['units']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'quantity_2', 'value'),
                         (Parent.Meta.attributes['quantity_2'], Quantity.Meta.attributes['value']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'quantity_2', 'units'),
                         (Parent.Meta.attributes['quantity_2'], Quantity.Meta.attributes['units']))
        self.assertEqual(utils.get_attribute_by_name(Parent, None, 'value'), (None, Parent.Meta.attributes['value']))
        self.assertEqual(utils.get_attribute_by_name(Parent, None, 'units'), (None, Parent.Meta.attributes['units']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'Quantity 1', 'Value', verbose_name=True),
                         (Parent.Meta.attributes['quantity_1'], Quantity.Meta.attributes['value']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'Quantity 1', 'Units', verbose_name=True),
                         (Parent.Meta.attributes['quantity_1'], Quantity.Meta.attributes['units']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'Quantity 2', 'Value', verbose_name=True),
                         (Parent.Meta.attributes['quantity_2'], Quantity.Meta.attributes['value']))
        self.assertEqual(utils.get_attribute_by_name(Parent, 'Quantity 2', 'Units', verbose_name=True),
                         (Parent.Meta.attributes['quantity_2'], Quantity.Meta.attributes['units']))
        self.assertEqual(utils.get_attribute_by_name(Parent, None, 'Value', verbose_name=True), (None, Parent.Meta.attributes['value']))
        self.assertEqual(utils.get_attribute_by_name(Parent, None, 'Units', verbose_name=True), (None, Parent.Meta.attributes['units']))

    def test_group_objects_by_model(self):
        (root, nodes, leaves) = (self.root, self.nodes, self.leaves)
        objects = [root] + nodes + leaves
        for grouped_objects in [
                utils.group_objects_by_model(objects),
                utils.group_objects_by_model(objects + nodes)]:
            self.assertEqual(grouped_objects[Root], [root])
            self.assertEqual(set(grouped_objects[Node]), set(nodes))
            self.assertEqual(set(grouped_objects[Leaf]), set(leaves))

    def test_get_related_errors(self):
        (root, nodes, leaves) = (self.root, self.nodes, self.leaves)

        errors = utils.get_related_errors(root)
        self.assertEqual(set((x.object for x in errors.invalid_objects)), set((root, )) | set(nodes))

        errors_by_model = errors.get_object_errors_by_model()
        self.assertEqual(set((x.__name__ for x in errors_by_model.keys())), set(('Root', 'Node')))

        self.assertEqual(len(errors_by_model[Root]), 1)
        self.assertEqual(len(errors_by_model[Node]), 2)

        self.assertIsInstance(str(errors), str)

    def test_get_related_errors_no_related(self):
        class LoneNode(core.Model):
            id = core.StringAttribute(max_length=1, primary=True, unique=True, verbose_name='Identifier')

        node = LoneNode(id='l')
        errors = utils.get_related_errors(node)
        self.assertEqual(errors, None)

        node = LoneNode(id='lone_node')
        errors = utils.get_related_errors(node)
        self.assertEqual([invalid_obj.object for invalid_obj in errors.invalid_objects], [node])

    def test_get_component_by_id(self):
        class Test(core.Model):
            val = core.StringAttribute()

        (root, nodes, leaves) = (self.root, self.nodes, self.leaves)
        self.assertEqual(utils.get_component_by_id(nodes, 'node-0'), nodes[0])
        self.assertEqual(utils.get_component_by_id(nodes, 'node-1'), nodes[1])
        self.assertEqual(utils.get_component_by_id(nodes, 'x'), None)

        test = Test(val='x')
        self.assertRaises(AttributeError,
                          lambda: utils.get_component_by_id([test], 'x'))
        self.assertEqual(utils.get_component_by_id([test], 'x', identifier='val'), test)

    def test_randomize(self):
        class NormNodeLevel0(core.Model):
            label = core.StringAttribute(primary=True, unique=True)

        class NormNodeLevel1(core.Model):
            label = core.StringAttribute(primary=True, unique=True)
            parents = core.ManyToManyAttribute(NormNodeLevel0, related_name='children')

        class NormNodeLevel2(core.Model):
            label = core.StringAttribute(primary=True, unique=True)
            parents = core.ManyToManyAttribute(NormNodeLevel1, related_name='children')

        nodes0 = []
        nodes1 = []
        nodes2 = []
        n = 20
        for i in range(n):
            nodes0.append(NormNodeLevel0(label='node_0_{}'.format(i)))

        for i in range(n):
            nodes1.append(NormNodeLevel1(label='node_1_{}'.format(i), parents=[
                          nodes0[(i) % n], nodes0[(i + 1) % n], nodes0[(i + 2) % n], ]))

        for i in range(n):
            nodes2.append(NormNodeLevel2(label='node_2_{}'.format(i), parents=[
                          nodes1[(i) % n], nodes1[(i + 1) % n], nodes1[(i + 2) % n], ]))

        def check_sorted():
            for i in range(n):
                i_childs = sorted([(i - 2) % n, (i - 1) % n, (i - 0) % n, ])
                for i_child, child in zip(i_childs, nodes0[i].children):
                    if child.label != 'node_1_{}'.format(i_child):
                        return False

                i_parents = sorted([(i + 0) % n, (i + 1) % n, (i + 2) % n, ])
                for i_parent, parent in zip(i_parents, nodes1[i].parents):
                    if parent.label != 'node_0_{}'.format(i_parent):
                        return False

                i_childs = sorted([(i - 2) % n, (i - 1) % n, (i - 0) % n, ])
                for i_child, child in zip(i_childs, nodes1[i].children):
                    if child.label != 'node_2_{}'.format(i_child):
                        return False

                i_parents = sorted([(i + 0) % n, (i + 1) % n, (i + 2) % n, ])
                for i_parent, parent in zip(i_parents, nodes2[i].parents):
                    if parent.label != 'node_1_{}'.format(i_parent):
                        return False

                return True

        # sort and check sorted
        nodes0[0].normalize()
        self.assertTrue(check_sorted())

        # randomize
        n_random = 0
        n_trials = 100
        for i in range(n_trials):
            utils.randomize_object_graph(nodes0[0])
            n_random += (check_sorted() == False)

            nodes0[0].normalize()
            self.assertTrue(check_sorted())

        self.assertGreater(n_random, 0.9 * n_trials)


class TestMetadata(unittest.TestCase):

    def setUp(self):
        self.tmp_dirname = tempfile.mkdtemp()

        # prepare test data repo
        self.github_test_data_repo = GitHubRepoForTests('test_data_repo')
        self.test_data_repo_dir = os.path.join(self.tmp_dirname, 'test_data_repo')
        os.mkdir(self.test_data_repo_dir)
        self.test_data_repo = self.github_test_data_repo.make_test_repo(self.test_data_repo_dir)

        # prepare test schema repo
        test_schema_repo_url = 'https://github.com/KarrLab/obj_tables_test_schema_repo'
        self.test_schema_repo_dir = os.path.join(self.tmp_dirname, 'test_schema_repo')
        test_schema_repo = git.Repo.clone_from(test_schema_repo_url, self.test_schema_repo_dir)

        # put schema dir on sys.path
        sys.path.append(self.test_schema_repo_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

        # clean up
        self.github_test_data_repo.delete_test_repo()

        # remove self.test_schema_repo_dir from sys.path
        for idx in range(len(sys.path) - 1, -1, -1):
            if sys.path[idx] == self.test_schema_repo_dir:
                del sys.path[idx]

    def test_set_git_repo_metadata_from_path(self):

        # get & test git metadata
        path = os.path.join(self.test_data_repo_dir, 'test.xlsx')
        data_repo_metadata = DataRepoMetadata()
        unsuitable_changes = utils.set_git_repo_metadata_from_path(data_repo_metadata,
                                                                   RepoMetadataCollectionType.DATA_REPO,
                                                                   path=path)
        self.assertEqual(unsuitable_changes, [])
        self.assertEqual(data_repo_metadata.url, 'https://github.com/KarrLab/test_data_repo.git')
        self.assertEqual(data_repo_metadata.branch, 'main')
        self.assertTrue(isinstance(data_repo_metadata.revision, str))
        self.assertEqual(len(data_repo_metadata.revision), 40)

    def test_set_git_repo_metadata_from_path_error(self):

        data_repo_metadata = DataRepoMetadata()
        self.assertEqual(data_repo_metadata.url, '')

        with self.assertRaisesRegex(ValueError, 'is not in a Git repository'):
            utils.set_git_repo_metadata_from_path(data_repo_metadata,
                                                  RepoMetadataCollectionType.SCHEMA_REPO,
                                                  path=self.tmp_dirname)
        self.assertEqual(data_repo_metadata.url, '')

    def test_read_metadata_from_file(self):
        # use fixtures to keep this code simple
        # test .xlsx files
        metadata_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'metadata')
        expected_xlsx_metadata = {
            'both-metadata.xlsx': (DataRepoMetadata, SchemaRepoMetadata),
            'data-repo-metadata.xlsx': (DataRepoMetadata, type(None)),
            'no-metadata.xlsx': (type(None), type(None)),
            'schema-repo-metadata.xlsx': (type(None), SchemaRepoMetadata)
        }
        for filename, expected_metadata_types in expected_xlsx_metadata.items():
            pathname = os.path.join(metadata_dir, filename)
            data_file_metadata = utils.read_metadata_from_file(pathname)
            actual_data_file_metadata_types = \
                (type(data_file_metadata.data_repo_metadata), type(data_file_metadata.schema_repo_metadata))
            self.assertEqual(actual_data_file_metadata_types, expected_metadata_types)

        # test .csv file
        csv_pathname = os.path.join(metadata_dir, 'csv_metadata', 'test*.csv')
        data_file_metadata = utils.read_metadata_from_file(csv_pathname)
        self.assertTrue(isinstance(data_file_metadata.data_repo_metadata, DataRepoMetadata))
        self.assertTrue(isinstance(data_file_metadata.schema_repo_metadata, SchemaRepoMetadata))
        for metadata in data_file_metadata:
            self.assertTrue(metadata.url.startswith('https://github.com/'))
            self.assertEqual(metadata.branch, 'master')
            self.assertTrue(isinstance(metadata.revision, str))
            self.assertEqual(len(metadata.revision), 40)

        # test exceptions
        with self.assertRaisesRegex(ValueError, "Multiple instances of .+ found in"):
            pathname = os.path.join(metadata_dir, 'extra-schema-metadata.xlsx')
            utils.read_metadata_from_file(pathname)

    def test_add_metadata_to_file(self):
        class Model1(core.Model):
            id = core.SlugAttribute()

        metadata_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'metadata')
        shutil.copy(os.path.join(metadata_dir, 'no-metadata.xlsx'), self.test_data_repo_dir)
        pathname = os.path.join(self.test_data_repo_dir, 'no-metadata.xlsx')

        metadata_path = utils.add_metadata_to_file(pathname, [Model1], schema_package='test_repo')
        data_file_metadata = utils.read_metadata_from_file(metadata_path)
        self.assertTrue(isinstance(data_file_metadata.data_repo_metadata, DataRepoMetadata))
        self.assertTrue(isinstance(data_file_metadata.schema_repo_metadata, SchemaRepoMetadata))
        for metadata in data_file_metadata:
            self.assertTrue(metadata.url.startswith('https://github.com/'))
            # currently, the data and schema repos have different branch names
            # make robust test that will work until master -> main transition ends
            # self.assertEqual(metadata.branch, 'master')
            self.assertIn(metadata.branch, ('master', 'main'))
            self.assertTrue(isinstance(metadata.revision, str))
            self.assertEqual(len(metadata.revision), 40)

    def test_get_attrs(self):
        attrs = utils.get_attrs()
        self.assertIn('String', attrs)
        self.assertNotIn('core.String', attrs)
        self.assertNotIn('core.StringAttribute', attrs)
        self.assertNotIn('StringAttribute', attrs)
        self.assertIn('chem.ChemicalFormula', attrs)


class InitSchemaTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

    def test_get_models(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, models = utils.init_schema('tests/fixtures/declarative_schema/schema.csv',
                                              out_filename=out_filename)
        self.assertEqual(set(models), set(utils.get_models(schema).values()))
        self.assertEqual(sorted(utils.get_models(schema).keys()),
                         ['Child', 'Parent', 'Quantity'])

        schema = utils.get_schema(out_filename)
        self.assertEqual(sorted(utils.get_models(schema).keys()),
                         ['Child', 'Parent', 'Quantity'])

    def test_rand_schema_name(self):
        name = utils.rand_schema_name(len=8)
        self.assertTrue(name.startswith('schema_'))
        self.assertEqual(len(name), len('schema_') + 8)

    def test_init_schema(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, _ = utils.init_schema('tests/fixtures/declarative_schema/schema.csv',
                                         out_filename=out_filename)

        p_0 = schema.Parent(id='p_0')
        c_0 = p_0.children.create(id='c_0')
        c_1 = p_0.children.create(id='c_1')
        c_2 = p_0.children.create(id='c_2')
        c_0._comments = ['A', 'B']
        c_1._comments = ['C', 'D']

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])
        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.is_equal(p_0))
        self.assertEqual(p_0_b.children.get_one(id='c_0')._comments, c_0._comments)
        self.assertEqual(p_0_b.children.get_one(id='c_1')._comments, c_1._comments)
        self.assertEqual(p_0_b.children.get_one(id='c_2')._comments, c_2._comments)

        # import module and test
        schema = utils.get_schema(out_filename)

        p_0 = schema.Parent(id='p_0')
        p_0.children.create(id='c_0')
        p_0.children.create(id='c_1')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])
        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.is_equal(p_0))

    def test_init_schema_from_xlsx(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema_csv = 'tests/fixtures/declarative_schema/schema*.csv'
        schema_xl = os.path.join(self.tmp_dirname, 'schema.xlsx')

        wb = wc_utils.workbook.io.read(schema_csv)
        wb['!!' + core.SCHEMA_SHEET_NAME] = wb.pop('')
        wc_utils.workbook.io.write(schema_xl, wb)

        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, _ = utils.init_schema(schema_xl,
                                         out_filename=out_filename)

        p_0 = schema.Parent(id='p_0')
        p_0.children.create(id='c_0')
        p_0.children.create(id='c_1')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])
        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.is_equal(p_0))

        # import module and test
        schema = utils.get_schema(out_filename)

        p_0 = schema.Parent(id='p_0')
        p_0.children.create(id='c_0')
        p_0.children.create(id='c_1')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])
        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.  is_equal(p_0))

        # invalid schema
        schema_xl_2 = os.path.join(self.tmp_dirname, 'schema-invalid.xlsx')

        wb = wc_utils.workbook.io.read(schema_xl)
        wb[core.SCHEMA_SHEET_NAME] = wb.pop('!!' + core.SCHEMA_SHEET_NAME)
        wc_utils.workbook.io.write(schema_xl_2, wb)
        with self.assertRaisesRegex(ValueError, 'must contain a sheet'):
            utils.init_schema(schema_xl_2,
                              out_filename=out_filename)

        wb = wc_utils.workbook.io.read(schema_xl)
        wb['!!' + core.SCHEMA_SHEET_NAME][0][0] = wb['!!' + core.SCHEMA_SHEET_NAME][0][0].replace(
            "type='{}'".format(core.SCHEMA_TABLE_TYPE), "id='{}'".format('my' + core.SCHEMA_TABLE_TYPE))
        wc_utils.workbook.io.write(schema_xl_2, wb)
        with self.assertRaisesRegex(ValueError, 'type of the schema must be'):
            utils.init_schema(schema_xl_2,
                              out_filename=out_filename)

        wb = wc_utils.workbook.io.read(schema_xl)
        wb['!!' + core.SCHEMA_SHEET_NAME][3][0] = wb['!!' + core.SCHEMA_SHEET_NAME][3][0] + '?'
        wc_utils.workbook.io.write(schema_xl_2, wb)
        with self.assertRaisesRegex(ValueError, 'names must consist of'):
            utils.init_schema(schema_xl_2,
                              out_filename=out_filename)

    def test_init_schema_from_csv_workbook(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema_csv = 'tests/fixtures/declarative_schema/schema*.csv'
        schema_csv_wb = os.path.join(self.tmp_dirname, 'schema-*.csv')

        wb = wc_utils.workbook.io.read(schema_csv)
        wb['!!' + core.SCHEMA_SHEET_NAME] = wb.pop('')
        wc_utils.workbook.io.write(schema_csv_wb, wb)

        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, _ = utils.init_schema(schema_csv_wb,
                                         out_filename=out_filename)

        p_0 = schema.Parent(id='p_0')
        p_0.children.create(id='c_0')
        p_0.children.create(id='c_1')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])
        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.is_equal(p_0))

        # import module and test
        schema = utils.get_schema(out_filename)

        p_0 = schema.Parent(id='p_0')
        p_0.children.create(id='c_0')
        p_0.children.create(id='c_1')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])
        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.is_equal(p_0))

    def test_init_schema_with_inheritance(self):
        csv_filename = os.path.join(self.tmp_dirname, 'schema.csv')
        py_filename = os.path.join(self.tmp_dirname, 'schema.py')

        ws_metadata = ['!!ObjTables',
                       "type='{}'".format(core.SCHEMA_TABLE_TYPE),
                       "description='Schema'",
                       "objTablesVersion='{}'".format(obj_tables.__version__),
                       ]
        col_headings = [
            '!Name',
            '!Type',
            '!Parent',
            '!Format',
            '!Description',
        ]

        rows = [
            '{}\n'.format(','.join(['ClsA1', 'Class', '', 'row', ''])),
            '{}\n'.format(','.join(['id_a1', 'Attribute', 'ClsA1', 'String', 'Id-a1'])),

            '{}\n'.format(','.join(['ClsA2', 'Class', 'ClsA1', 'row', ''])),
            '{}\n'.format(','.join(['id_a2', 'Attribute', 'ClsA2', 'String', 'Id-a2'])),

            '{}\n'.format(','.join(['ClsA30', 'Class', 'ClsA2', 'row', ''])),
            '{}\n'.format(','.join(['id_a30', 'Attribute', 'ClsA30', 'String', 'Id-a30'])),

            '{}\n'.format(','.join(['ClsA31', 'Class', 'ClsA2', 'row', ''])),
            '{}\n'.format(','.join(['id_a31', 'Attribute', 'ClsA31', 'String', 'Id-a31'])),

            '{}\n'.format(','.join(['ClsB1', 'Class', '', 'row', ''])),
            '{}\n'.format(','.join(['id_b1', 'Attribute', 'ClsB1', 'String', 'Id-b1'])),

            '{}\n'.format(','.join(['ClsB2', 'Class', 'ClsB1', 'row', ''])),
            '{}\n'.format(','.join(['id_b2', 'Attribute', 'ClsB2', 'String', 'Id-b2'])),

            '{}\n'.format(','.join(['ClsB30', 'Class', 'ClsB2', 'row', ''])),
            '{}\n'.format(','.join(['id_b30', 'Attribute', 'ClsB30', 'String', 'Id-b30'])),

            '{}\n'.format(','.join(['ClsB31', 'Class', 'ClsB2', 'row', ''])),
            '{}\n'.format(','.join(['id_b31', 'Attribute', 'ClsB31', 'String', 'Id-b31'])),
        ]

        with open(csv_filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write(''.join(rows))

        schema, _, _ = utils.init_schema(csv_filename, out_filename=py_filename)
        b31 = schema.ClsB31(id_b1='l1', id_b2='l2', id_b31='l3')
        self.assertEqual(b31.id_b1, 'l1')
        self.assertEqual(b31.id_b2, 'l2')
        self.assertEqual(b31.id_b31, 'l3')
        self.assertIsInstance(b31, schema.ClsB31)
        self.assertIsInstance(b31, schema.ClsB2)
        self.assertIsInstance(b31, schema.ClsB1)
        self.assertIsInstance(b31, obj_tables.Model)
        self.assertNotIsInstance(b31, schema.ClsA31)

        self.assertEqual(set(get_subclasses(schema.ClsA1)), set([schema.ClsA2, schema.ClsA30, schema.ClsA31]))
        self.assertEqual(set(get_subclasses(schema.ClsA2)), set([schema.ClsA30, schema.ClsA31]))
        self.assertEqual(set(get_subclasses(schema.ClsA30)), set())

        # check that Python file generated correctly
        schema = utils.get_schema(py_filename)
        b31 = schema.ClsB31(id_b1='l1', id_b2='l2', id_b31='l3')
        self.assertEqual(b31.id_b1, 'l1')
        self.assertEqual(b31.id_b2, 'l2')
        self.assertEqual(b31.id_b31, 'l3')
        self.assertEqual(set(get_subclasses(schema.ClsA1)), set([schema.ClsA2, schema.ClsA30, schema.ClsA31]))

        # check that definition works with random order of rows
        with open(csv_filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            for i_row in numpy.random.permutation(len(rows)):
                file.write(rows[i_row])

        schema, _, _ = utils.init_schema(csv_filename)
        b31 = schema.ClsB31(id_b1='l1', id_b2='l2', id_b31='l3')
        self.assertEqual(b31.id_b1, 'l1')
        self.assertEqual(b31.id_b2, 'l2')
        self.assertEqual(b31.id_b31, 'l3')
        self.assertEqual(set(get_subclasses(schema.ClsA1)), set([schema.ClsA2, schema.ClsA30, schema.ClsA31]))

    def test_init_schema_errors(self):
        with self.assertRaisesRegex(ValueError, 'format is not supported'):
            utils.init_schema(os.path.join(self.tmp_dirname, 'schema.txt'))

        filename = os.path.join(self.tmp_dirname, 'schema.csv')
        ws_metadata = ['!!ObjTables',
                       "type='{}'".format(core.SCHEMA_TABLE_TYPE),
                       "description='Schema'",
                       "objTablesVersion='{}'".format(obj_tables.__version__),
                       ]

        col_headings = [
            '!Name',
            '!Type',
            '!Parent',
            '!Format',
            '!Description',
        ]

        with open(filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write('{}\n'.format(','.join(['Cls1', 'Class', 'Cls2', 'column', ''])))
            file.write('{}\n'.format(','.join(['Cls2', 'Class', 'Cls1', 'column', ''])))
        with self.assertRaisesRegex(ValueError, 'must be acyclic'):
            utils.init_schema(filename)

        with open(filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write('{}\n'.format(','.join(['Attr1', 'Attribute', 'Cls1', 'String', 'attr1'])))
            file.write('{}\n'.format(','.join(['Attr1', 'Attribute', 'Cls1', 'String', 'attr2'])))
        with self.assertRaisesRegex(ValueError, 'can only be defined once'):
            utils.init_schema(filename)

        with open(filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write('{}\n'.format(','.join(['1Cls', 'Class', '', 'row', ''])))
        with self.assertRaisesRegex(ValueError, 'must start'):
            utils.init_schema(filename)

        with open(filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write('{}\n'.format(','.join(['Attr1', 'Attribute', '1Cls', 'String', 'attr2'])))
        with self.assertRaisesRegex(ValueError, 'must start'):
            utils.init_schema(filename)

        with open(filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write('{}\n'.format(','.join(['Cls1', 'Class', '', 'row', ''])))
            file.write('{}\n'.format(','.join(['Cls1', 'Class', '', 'row', ''])))
        with self.assertRaisesRegex(ValueError, 'can only be defined once'):
            utils.init_schema(filename)

        with open(filename, 'w') as file:
            file.write('{}\n'.format(' '.join(ws_metadata)))
            file.write('{}\n'.format(','.join(col_headings)))
            file.write('{}\n'.format(','.join(['Cls1', 'Unsupported', 'Doc', 'column', ''])))
        with self.assertRaisesRegex(ValueError, 'is not supported'):
            utils.init_schema(filename)

    def test_extra_sheets(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, _ = utils.init_schema('tests/fixtures/declarative_schema/schema.csv',
                                         out_filename=out_filename)

        p_0 = schema.Parent(id='p_0')
        c_0 = p_0.children.create(id='c_0')
        c_1 = p_0.children.create(id='c_1')
        c_2 = p_0.children.create(id='c_2')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])

        wb = wc_utils.workbook.io.read(filename)
        wb['Extra'] = wc_utils.workbook.Worksheet()
        wb['Extra'].append(wc_utils.workbook.Row([
            "!!ObjTables type='Data' class='Extra' objTablesVersion='{}'".format(
                obj_tables.__version__)]))
        wb['!!' + core.SCHEMA_SHEET_NAME] = wc_utils.workbook.Worksheet()
        wb['!!' + core.SCHEMA_SHEET_NAME].append(wc_utils.workbook.Row([
            "!!ObjTables type='{}' objTablesVersion='{}'".format(
                core.SCHEMA_TABLE_TYPE, obj_tables.__version__)]))
        wc_utils.workbook.io.write(filename, wb)

        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]
        self.assertTrue(p_0_b.is_equal(p_0))

        wb = wc_utils.workbook.io.read(filename)
        wb['!!Extra'] = wb.pop('Extra')
        wc_utils.workbook.io.write(filename, wb)
        with self.assertRaisesRegex(ValueError, 'No matching models'):
            obj_tables.io.WorkbookReader().run(
                filename,
                models=[schema.Parent, schema.Child])

    def test_extra_attributes(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, _ = utils.init_schema('tests/fixtures/declarative_schema/schema.csv',
                                         out_filename=out_filename)

        p_0 = schema.Parent(id='p_0')
        c_0 = p_0.children.create(id='c_0')
        c_1 = p_0.children.create(id='c_1')
        c_2 = p_0.children.create(id='c_2')

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])

        wb = wc_utils.workbook.io.read(filename)
        wb['!!Child'][2].append('!Extra')
        wc_utils.workbook.io.write(filename, wb)

        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child],
            ignore_extra_attributes=True)[schema.Parent][0]
        self.assertTrue(p_0_b.is_equal(p_0))

        with self.assertRaisesRegex(ValueError, 'does not match any attribute'):
            obj_tables.io.WorkbookReader().run(
                filename,
                models=[schema.Parent, schema.Child],
                ignore_extra_attributes=False)[schema.Parent][0]

        wb = wc_utils.workbook.io.read(filename)
        wb['!!Child'][2][-1] = '!Extra'
        wc_utils.workbook.io.write(filename, wb)
        obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child],
            ignore_extra_attributes=True)[schema.Parent][0]
        with self.assertRaisesRegex(ValueError, 'does not match any attribute'):
            obj_tables.io.WorkbookReader().run(
                filename,
                models=[schema.Parent, schema.Child],
                ignore_extra_attributes=False)[schema.Parent][0]

    def test_comments(self):
        out_filename = os.path.join(self.tmp_dirname, 'schema.py')
        schema, _, _ = utils.init_schema('tests/fixtures/declarative_schema/schema.csv',
                                         out_filename=out_filename)

        p_0 = schema.Parent(id='p_0')
        p_0._comments = ['X', 'Y']
        c_0 = p_0.children.create(id='c_0')
        c_1 = p_0.children.create(id='c_1')
        c_2 = p_0.children.create(id='c_2')
        c_0._comments = ['A', 'B']
        c_1._comments = ['C', 'D']

        filename = os.path.join(self.tmp_dirname, 'data.xlsx')
        obj_tables.io.WorkbookWriter().run(
            filename, [p_0],
            models=[schema.Parent, schema.Child])

        wb = wc_utils.workbook.io.read(filename)
        wb['!!Parent'].insert(0, wc_utils.workbook.Row(['%/ V /%']))
        wb['!!Parent'].insert(0, wc_utils.workbook.Row([]))
        wb['!!Parent'].insert(3, wc_utils.workbook.Row([]))
        wb['!!Parent'].insert(3, wc_utils.workbook.Row(['%/ W /%']))
        wb['!!Parent'][5].append('%/ Z /%')
        wb['!!Child'].insert(0, wc_utils.workbook.Row(['%/ 123 /%']))
        wb['!!Child'].append(wc_utils.workbook.Row(['%/ 456 /%']))
        wc_utils.workbook.io.write(filename, wb)

        p_0_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[schema.Parent, schema.Child])[schema.Parent][0]

        self.assertTrue(p_0_b.is_equal(p_0))
        self.assertEqual(p_0_b._comments, ['V', 'W'] + p_0._comments + ['Z'])
        self.assertEqual(p_0_b.children.get_one(id='c_0')._comments, ['123'] + c_0._comments)
        self.assertEqual(p_0_b.children.get_one(id='c_1')._comments, c_1._comments)
        self.assertEqual(p_0_b.children.get_one(id='c_2')._comments, c_2._comments + ['456'])

    def test_write_schema(self):
        class Parent(core.Model):
            id = core.SlugAttribute()
            name = core.StringAttribute()

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'name')
                table_format = core.TableFormat.column

        class Child(core.Model):
            id = core.SlugAttribute()
            name = core.StringAttribute()
            parents = core.ManyToManyAttribute(Parent, related_name='children')

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'name', 'parents')

        p_1 = Parent(id='p_1', name='p 1')
        p_1.children.create(id='c_1', name='c 1')
        p_1.children.create(id='c_2', name='c 2')

        # to XLSX
        filename = os.path.join(self.tmp_dirname, 'test.xlsx')

        obj_tables.io.WorkbookWriter().run(
            filename,
            [p_1],
            models=[Parent, Child],
            write_schema=True)

        wb = wc_utils.workbook.io.read(filename)
        self.assertIn('!!' + obj_tables.io.SCHEMA_SHEET_NAME, wb)

        p_1_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[Parent, Child],
            group_objects_by_model=True)[Parent][0]
        self.assertTrue(p_1_b.is_equal(p_1))

        # to csv
        filename = os.path.join(self.tmp_dirname, 'test-*.csv')

        obj_tables.io.WorkbookWriter().run(
            filename,
            [p_1],
            models=[Parent, Child],
            write_schema=True)

        wb = wc_utils.workbook.io.read(filename)
        self.assertIn(obj_tables.io.SCHEMA_SHEET_NAME, wb)

        p_1_b = obj_tables.io.WorkbookReader().run(
            filename,
            models=[Parent, Child],
            group_objects_by_model=True)[Parent][0]
        self.assertTrue(p_1_b.is_equal(p_1))

    def test__get_tabular_schema_format(self):
        attr = core.UrlAttribute(primary=True, unique=True)
        self.assertEqual(attr._get_tabular_schema_format(), 'Url(primary=True, unique=True)')


class ToPandasTestCase(unittest.TestCase):
    def test(self):
        class Child(core.Model):
            id = core.SlugAttribute(verbose_name='Id')
            name = core.StringAttribute(verbose_name='Name')

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'name')
                verbose_name = 'Child'
                verbose_name_plural = 'Child'

        class Parent(core.Model):
            id = core.SlugAttribute(verbose_name='Id')
            name = core.StringAttribute(verbose_name='Name')
            children = core.ManyToManyAttribute(Child, related_name='parents',
                                                verbose_name='Children')

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'name', 'children')
                verbose_name = 'Parent'
                verbose_name_plural = 'Parent'

        p_0 = Parent(id='p_0')
        p_0.children.create(id='c_0')
        p_0.children.create(id='c_1')
        p_0.children.create(id='c_2')

        dfs = utils.to_pandas([p_0], models=[Parent, Child])
        self.assertEqual(dfs[Parent].columns.tolist(), ['Id', 'Name', 'Children'])
        self.assertEqual(dfs[Child].columns.tolist(), ['Id', 'Name'])
        self.assertEqual(dfs[Parent].values.tolist(), [['p_0', '', 'c_0, c_1, c_2']])
        self.assertEqual(dfs[Child].values.tolist(), [['c_0', ''], ['c_1', ''], ['c_2', '']])

    def test_multicell(self):
        class Child(core.Model):
            id = core.SlugAttribute(verbose_name='Id')
            name = core.StringAttribute(verbose_name='Name')

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'name')
                table_format = core.TableFormat.multiple_cells
                verbose_name = 'Child'
                verbose_name_plural = 'Child'

        class Parent(core.Model):
            id = core.SlugAttribute(verbose_name='Id')
            name = core.StringAttribute(verbose_name='Name')
            child = core.ManyToOneAttribute(Child, related_name='parents',
                                            verbose_name='Child')

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'name', 'child')
                verbose_name = 'Parent'
                verbose_name_plural = 'Parent'

        p_0 = Parent(id='p_0')
        p_0.child = Child(id='c_0')
        p_1 = Parent(id='p_1')
        p_1.child = Child(id='c_1')

        dfs = utils.to_pandas([p_0, p_1], models=[Parent, Child])
        numpy.testing.assert_array_equal(dfs[Parent].columns.tolist(), [
            (float('nan'), 'Id'),
            (float('nan'), 'Name'),
            ('Child', 'Id'),
            ('Child', 'Name'),
        ])
        self.assertNotIn(Child, dfs)
        self.assertEqual(dfs[Parent].values.tolist(), [
            ['p_0', '', 'c_0', ''],
            ['p_1', '', 'c_1', ''],
        ])


class VizSchemaTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test(self):
        schema, _, _ = utils.init_schema('tests/fixtures/declarative_schema/schema.csv')
        filename = os.path.join(self.dirname, 'test.svg')
        utils.viz_schema(schema, filename)
        self.assertTrue(os.path.isfile(filename))

        schema, _, _ = utils.init_schema('tests/fixtures/declarative_schema/viz_schema.csv')
        filename = os.path.join(self.dirname, 'test.svg')
        utils.viz_schema(schema, filename)
        self.assertTrue(os.path.isfile(filename))
