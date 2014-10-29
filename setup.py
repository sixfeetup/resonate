from setuptools import setup, find_packages
import os

version = '1.21'

long_description = (
    open('README.txt').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.txt').read()
    + '\n' +
    open('CHANGES.txt').read()
    + '\n')

setup(name='resonate',
      version=version,
      description="Package for syndicating content between micro-sites.",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='gpl',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'p4a.subtyper',
          'zc.queue',
          'sixfeetup.utils',
          'sixfeetup.workflow.chained',
          'plone.app.dexterity',
          'collective.js.chosen',
          'collective.lineage',
          'z3c.relationfield',
          'plone.directives.form',
          'plone.formwidget.contenttree',
          'archetypes.schemaextender',
          'archetypes.referencebrowserwidget',
          'Products.OrderableReferenceField',
      ],
      extras_require={'test': ['plone.app.testing']},
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      [console_scripts]
      create_syndication_digest = resonate.scripts.digest:create_digest
      """,
      )
