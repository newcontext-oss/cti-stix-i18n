What should the API be like.
============================

There needs to be a wrapper object that you set the current language.
The wrapper object needs to either be given objects, or have a method
of lookup and fetch.

Likely just via a wrapper style object.

x - test added
o - test needed

For reading:
x -- o = stixlangwrap('en', obj)
x -- o = stixlangwrap([ 'jp', 'en' ], obj)
x -- o.addtranslationobject(obj2)
x -- o.description
x -- o.getlangtext('description')

o -- ostore = stixlangwrap('en', fetchfun)
o -- o = ostore['uuid']

will fetch translation objects, and use a translation
if available, along with a priority list


For writing

how to decide to handle revising a translation object.
Can you change/translation the native language of the object?


Test cases
==========

Simple
------

read one language from an object w/ a translation object
write translations to a new object
translation of list properties

Complex
-------

read a priority of languages from an object w/ a translation object
read a priority of languages from an object w/ multipl translation objects
translation of list properties with multiple languages that are mixed (e.g.
some translated to jp, some es, etc)


Questions
=========

1. How to layer translations?  If you want to "include" another translation, do you copy the fields?


Resources
=========


Trey's workbook: https://github.com/treyka/stix2-jupyter/blob/master/STIX%202.1%20Preview.ipynb
My clone: https://github.com/jmgnc/stix2-jupyter/blob/master/STIX%202.1%20Preview.ipynb
