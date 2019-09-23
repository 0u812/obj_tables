""" Test examples

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2019-09-18
:Copyright: 2019, Karr Lab
:License: MIT
"""

from obj_tables import __main__
from obj_tables import io
from obj_tables import utils
import obj_tables
import os
import unittest


class ExamplesTestCase(unittest.TestCase):
    def test_web_app_example(self):
        filename = 'examples/parents_children.xlsx'

        schema = utils.init_schema(filename)
        models = list(utils.get_models(schema).values())

        io.Reader().run(filename,
                        models=models,
                        group_objects_by_model=False,
                        ignore_sheet_order=True)

        #########################
        # import parents_children
        parents_children = schema

        #########################
        # Create parents
        jane_doe = parents_children.Parent(id='jane_doe', name='Jane Doe')
        john_doe = parents_children.Parent(id='john_doe', name='John Doe')
        mary_roe = parents_children.Parent(id='mary_roe', name='Mary Roe')
        richard_roe = parents_children.Parent(id='richard_roe', name='Richard Roe')

        # Create children
        jamie_doe = parents_children.Child(id='jamie_doe',
                                           name='Jamie Doe',
                                           gender=parents_children.Child.gender.enum_class.female,
                                           parents=[jane_doe, john_doe])
        jamie_doe.favorite_video_game = parents_children.Game(name='Legend of Zelda: Ocarina of Time',
                                                              publisher='Nintendo',
                                                              year=1998)

        jimie_doe = parents_children.Child(id='jimie_doe',
                                           name='Jimie Doe',
                                           gender=parents_children.Child.gender.enum_class.male,
                                           parents=[jane_doe, john_doe])
        jimie_doe.favorite_video_game = parents_children.Game(name='Super Mario Brothers',
                                                              publisher='Nintendo',
                                                              year=1985)
        linda_roe = parents_children.Child(id='linda_roe',
                                           name='Linda Roe',
                                           gender=parents_children.Child.gender.enum_class.female,
                                           parents=[mary_roe, richard_roe])
        linda_roe.favorite_video_game = parents_children.Game(name='Sonic the Hedgehog',
                                                              publisher='Sega',
                                                              year=1991)
        mike_roe = parents_children.Child(id='mike_roe',
                                          name='Michael Roe',
                                          gender=parents_children.Child.gender.enum_class.male,
                                          parents=[mary_roe, richard_roe])
        mike_roe.favorite_video_game = parents_children.Game(name='SimCity',
                                                             publisher='Electronic Arts',
                                                             year=1989)

        #########################
        mike_roe = mary_roe.children.get_one(id='mike_roe')
        mikes_parents = mike_roe.parents
        mikes_sisters = mikes_parents[0].children.get(gender=parents_children.Child.gender.enum_class.female)

        #########################
        jamie_doe.favorite_video_game.name = 'Legend of Zelda'
        jamie_doe.favorite_video_game.year = 1986

        #########################
        import obj_tables

        objects = [jane_doe, john_doe, mary_roe, richard_roe,
                   jamie_doe, jimie_doe, linda_roe, mike_roe]
        errors = obj_tables.Validator().run(objects)
        assert errors is None

        #########################
        import obj_tables.io

        filename = 'examples/parents_children.xlsx'
        objects = obj_tables.io.Reader().run(filename,
                                             models=[parents_children.Parent, parents_children.Child],
                                             group_objects_by_model=True,
                                             ignore_sheet_order=True)
        parents = objects[parents_children.Parent]
        jane_doe_2 = next(parent for parent in parents if parent.id == 'jane_doe')

        #########################
        filename = 'examples/parents_children_copy.xlsx'
        objects = [jane_doe, john_doe, mary_roe, richard_roe,
                   jamie_doe, jimie_doe, linda_roe, mike_roe]
        obj_tables.io.Writer().run(filename, objects,
                                   models=[parents_children.Parent, parents_children.Child])

        #########################
        assert jane_doe.is_equal(jane_doe_2)

        #########################
        # cleanup
        os.remove(filename)

    def test_biochemical_model_example(self):
        schema_filename = 'examples/biochemical_models/schema.csv'

        py_module_filename = 'examples/biochemical_models/schema.py'
        with __main__.App(argv=['init-schema', schema_filename, py_module_filename]) as app:
            app.run()

        template_filename = 'examples/biochemical_models/template.xlsx'
        with __main__.App(argv=['gen-template', schema_filename, template_filename, '--write-schema']) as app:
            app.run()

        data_filename = 'examples/biochemical_models/data.xlsx'
        with __main__.App(argv=['validate', schema_filename, data_filename]) as app:
            app.run()

        data_copy_filename = 'examples/biochemical_models/data_copy.xlsx'
        with __main__.App(argv=['convert', schema_filename, data_filename, data_copy_filename, '--write-schema']) as app:
            app.run()

        with __main__.App(argv=['diff', schema_filename, 'Model', data_filename, data_copy_filename]) as app:
            app.run()

    def test_sbtab_sbml_validate_examples(self):
        self.do_sbtab_sbml_examples('validate')

    def test_sbtab_sbml_convert_examples(self):
        self.do_sbtab_sbml_examples('convert')

    def do_sbtab_sbml_examples(self, action):
        schema_filename = 'examples/sbtab-sbml/schema.csv'

        # Initalize Python module which implements schema
        py_module_filename = 'examples/sbtab-sbml/schema.py'
        with __main__.App(argv=['init-schema', schema_filename, py_module_filename]) as app:
            app.run()

        # Generate a template for the schema
        template_filename = 'examples/sbtab-sbml/template.xlsx'
        with __main__.App(argv=['gen-template', schema_filename, template_filename]) as app:
            app.run()

        # Validate that documents adhere to the schema
        data_filenames = [
            # 'template.xlsx',
            'hynne/*.tsv',
            'hynne.multi.tsv',
            'lac_operon/*.tsv',
            'feed_forward_loop_relationship.tsv',
            'kegg_reactions_cc_ph70_quantity.tsv',
            'yeast_transcription_network_chang_2008_relationship.tsv',
            'simple_examples/1.multi.tsv',
            'simple_examples/2.multi.csv',
            'simple_examples/3.multi.csv',
            'simple_examples/4.multi.csv',
            'simple_examples/5.multi.csv',
            'simple_examples/6.multi.csv',
            'simple_examples/7.csv',
            'simple_examples/8.csv',
            'simple_examples/9.csv',
            'simple_examples/10.csv',
            'teusink_data.tsv',
            'teusink_model.multi.tsv',
            'jiang_data.tsv',
            'jiang_model.multi.tsv',
            'ecoli_noor_2016_data.tsv',
            'ecoli_noor_2016_model.multi.tsv',
            'ecoli_wortel_2018_data.tsv',
            'ecoli_wortel_2018_model.multi.tsv',
            'sigurdsson_model.multi.tsv',
            'layout_model.multi.tsv',
        ]
        for data_filename in data_filenames:
            full_data_filename = os.path.join('examples', 'sbtab-sbml', data_filename)

            if action == 'validate':
                with __main__.App(argv=['validate', schema_filename, full_data_filename]) as app:
                    app.run()

            if action == 'convert' and not data_filename.endswith('.xlsx'):
                convert_filename = data_filename \
                    .replace('/*', '') \
                    .replace('.csv', '.xlsx') \
                    .replace('.tsv', '.xlsx')
                full_convert_filename = os.path.join('examples', 'sbtab-sbml', convert_filename)
                with __main__.App(argv=['convert', schema_filename, full_data_filename,
                                        full_convert_filename, ]) as app:
                    app.run()
