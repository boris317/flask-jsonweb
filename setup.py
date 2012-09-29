from setuptools import setup, find_packages
import sys, os

version = '0.3'

setup(name='Flask-JsonWeb',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Shawn Adams',
      author_email='',
      url='',
      license='',
      py_modules=['flask_jsonweb'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "flask",
          "jsonweb==0.6.1"
      ],
      dependency_links=[
          "git+http://github.com/boris317/JsonWeb@0.6.1r2#egg=JsonWeb-0.6.1"      
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
