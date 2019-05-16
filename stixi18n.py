#!/usr/bin/env python
# -*- coding: utf-8
#
# Copyright 2018 New Context Services, Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from stix2.v21 import Campaign, CustomObject, Identity, LanguageContent
from stix2.v21.bundle import Bundle
from stix2 import properties
import stix2
import unittest

__copyright__ = 'Copyright 2018 New Context Services, Inc.'
__license__ = '2-clause BSD'
__maintainer__ = 'John-Mark Gurney'
__email__ = 'jmg@newcontext.com'

__all__ = [ 'stixlangwrap' ]

@CustomObject('x-bogus-lc', [ ('object_ref', properties.StringProperty()),
	])
class _BogusLC(object):
	pass

class stixlangwrap(object):
	'''Wrapper to make accessining and setting languages on STIX objects.'''

	def __init__(self, lang, obj, no_default=False):
		'''lang: either a string that is the default language, or a
			list of strings, with the earlier one preferred over
			the later ones.
		obj: A STIX object from the STIX 2 framework.
		no_default: Raise an Attribute error if one of the specified
			languages is not available.
		'''

		if isinstance(lang, basestring):
			self._lang = [ lang ]
		else:
			self._lang = list(lang)

		self._obj = obj
		self._transobj = []
		self._nodefault = no_default

	def recast(self, lang):
		'''Make a child translation object with a new set of language
		preferences.  It will mirror any added translation objects as
		the parent, and modifications (translations) will be treated
		the same as well.'''

		raise NotImplementedError

	def gettranslationobject(self):
		'''Return the most recent language-content object added, if any.'''

		if self._transobj:
			return self._transobj[0]

	def addtranslationobject(self, transobj=None, ident=None, bundle=None):
		'''
		Add or create a language-content object to layer over the STIX
		object.  Only one of the keyword arguments is allowed to be
		specified.

		transobj: Use the specified STIX object for translations
		ident: Create a new one using the specified ID as the
			created_by_ref contents
		bundle: Find and use the language-content object for the
			STIX object that is in the bundle.
		'''

		if sum(x is not None for x in (transobj, ident, bundle)) != 1:
			raise ValueError('one and only one of transobj, '
			    'ident or bundle MUST be specified')

		if ident is not None:
			# identity is specified
			transobj = LanguageContent(object_ref=self._obj.id,
			    object_modified=self._obj.modified,
			    contents={ 'bogus': {} }, created_by_ref=ident.id)

		if bundle is not None:
			try:
				transobj = [ x for x in bundle.objects if
				    x.type == 'language-content' and
				    hasattr(x, 'object_ref') and
				    x.object_ref == self._obj.id ][0]
			except IndexError:
				raise ValueError('unable to find '
				    'language-content object for %s' %
				    repr(self._obj.id))

		if transobj is not None:
			if transobj.type != 'language-content':
				raise ValueError('invalid type, expected '
				    'language-content, got: %s' % `transobj.type`)

			self._transobj.insert(0, transobj)

	def __getattr__(self, k):
		return self.getlangtext(k)[1]

	@staticmethod
	def _getlangmarking(obj, k):
		try:
			for marking in obj.granular_markings:
				for marking_selector in marking['selectors']:
					if k == marking_selector:
						try:
							return marking['lang']
						except KeyError:
							pass
		except Exception:
			pass

		raise ValueError('unable to find selector for "%s"' % `k`)

	def getlangtext(self, k):
		'''Return the language and the text of the attribute k as
		a tuple.  If a lang is not specified on the original object
		and there is not a more prefered translation for that property,
		None is returned for the language.

		This will search the most recently added translation objects
		first, and finally the base object.'''

		try:
			marklang = self._getlangmarking(self._obj, k)
		except ValueError:
			marklang = None

		for l in self._lang:
			# XXX - https://github.com/oasis-open/cti-python-stix2/issues/251
			# mark = self._obj.get_markings(k)
			if marklang == l:
				return l, getattr(self._obj, k)
			elif marklang is None:
				# only if there is no marking for the field
				if hasattr(self._obj, 'lang') and l == self._obj.lang:
					return l, getattr(self._obj, k)

			for x in self._transobj:
				if x is not None and \
				    l in x.contents and k in x.contents[l]:
					return l, x.contents[l][k]

		# fail to default
		if self._nodefault or marklang is not None:
			raise AttributeError(
			    'unable to find the text for: %s' % `k`)

		# xxx broken in granular markings
		return self._obj.lang if hasattr(self._obj, 'lang') else \
		    None, getattr(self._obj, k)

	def setlangtext(self, k, lang, v):
		'''Set a property on the most recently added translation
		object.

		This does not update the modified date of the object, and so
		when you output/serialize it, it is the caller's job to
		properly handle versioning.'''

		if not self._transobj:
			raise ValueError('no translation object set')

		self._transobj[0].contents.setdefault(lang, {})[k] = v

class TestSTIXi18n(unittest.TestCase):
	def setUp(self):
		self.ident = Identity(name="Testing",
		    identity_class="organization")

	def test_reading(self):
		name = 'A Campaign'
		desc = 'This is a basic description of a campaign.'
		camp = Campaign(name=name, lang='en', description=desc,
		    created_by_ref=self.ident.id)

		# that a simple language wrapper
		o = stixlangwrap('en', camp)

		# returns the parent descrption
		self.assertEqual(o.description, desc)

		# and the correct language
		self.assertEqual(o.getlangtext('description'), ('en', desc))

		o = stixlangwrap(['th', 'en'], camp)

		# that when a translaction object
		thdesc = 'A description in Thai.'
		transobj = LanguageContent(object_ref=camp.id,
		    object_modified=camp.modified, contents={ 'th':
		    { 'description': thdesc }}, created_by_ref=self.ident.id)

		# is added to a language wrapper w/ Thai as the priority
		o.addtranslationobject(transobj)

		# that the Thai description is returned
		self.assertEqual(o.description, thdesc)
		self.assertEqual(o.getlangtext('description'), ('th', thdesc))

		# that then a translation object does not have a translation for a
		# property, that it falls back to what is available
		self.assertEqual(o.getlangtext('name'), ('en', name))

		# That a Thai language wrapper
		o = stixlangwrap('th', camp)

		# with no translation, returns the English text
		self.assertEqual(o.description, desc)
		self.assertEqual(o.getlangtext('description'), ('en', desc))

		# That a Thai language wrapper, that does not want defaults
		o = stixlangwrap('th', camp, no_default=True)

		# w/o a translation

		# raises errors
		self.assertRaises(AttributeError, getattr, o, 'description')
		self.assertRaises(AttributeError, o.getlangtext, 'description')

		o = stixlangwrap(['th', 'en'], camp)

		# that when a translaction object
		thdesc = 'A description in Thai.'
		transobj = LanguageContent(object_ref=camp.id,
		    object_modified=camp.modified, contents={ 'th':
		    { 'description': thdesc }}, created_by_ref=self.ident.id)

		# is added to a language wrapper w/ Thai as the priority
		o.addtranslationobject(transobj)

		# and a second translaction object
		thname = 'A name in Thai.'
		transobj2 = LanguageContent(object_ref=camp.id,
		    object_modified=camp.modified, contents={ 'th':
		    { 'name': thname }}, created_by_ref=self.ident.id)

		# is added to a language wrapper w/ Thai as the priority
		o.addtranslationobject(transobj2)

		# that both translations are returned
		self.assertEqual(o.getlangtext('description'), ('th', thdesc))
		self.assertEqual(o.getlangtext('name'), ('th', thname))

	def test_nolang(self):
		desc = 'This is a basic description of a campaign.'
		camp = Campaign(name='A Campaign', description=desc,
		    created_by_ref=self.ident.id)

		o = stixlangwrap('th', camp)

		# that a campaign object w/o language, returns None as the
		# language
		self.assertEqual(o.getlangtext('description'), (None, desc))

	def test_failures(self):
		desc = 'This is a basic description of a campaign.'
		camp = Campaign(name='A Campaign', lang='en', description=desc,
		    created_by_ref=self.ident.id)

		o = stixlangwrap('en', camp)
		self.assertRaises(ValueError, o.addtranslationobject, camp)

		self.assertRaises(ValueError, o.addtranslationobject)
		self.assertRaises(ValueError, o.addtranslationobject, 1, 1)

	def test_writing(self):
		desc = 'This is a basic description of a campaign'
		camp = Campaign(name='A Campaign', lang='en', description=desc)

		o = stixlangwrap([ 'th', 'en' ], camp)

		# that an object w/o a translation object raise an error
		self.assertRaises(ValueError, o.setlangtext, 'description',
		    'th', 'foo')

		# that a translation object can be added
		o.addtranslationobject(ident=self.ident)

		# and that it can be fetched:
		transobj = o.gettranslationobject()

		# and that is is a properly formed object
		self.assertEqual(transobj.type, 'language-content')
		self.assertEqual(transobj.created_by_ref, self.ident.id)

		# and the English description is returned
		self.assertEqual(o.getlangtext('description'), ('en', desc))

		# that when a translation is set
		thdesc = 'a Thai description'
		o.setlangtext('description', 'th', thdesc)

		# that the translation is now returned
		self.assertEqual(o.getlangtext('description'), ('th', thdesc))

		transobj = o.gettranslationobject()

		# and the translation is in the correct location
		self.assertEqual(transobj.contents['th']['description'], thdesc)

	def test_import(self):
		# That an imported campaign object
		with open('test_camp.json') as fp:
			camp = stix2.parse(fp.read())

		# and an imported translation object
		with open('test_trans.json') as fp:
			transobj = stix2.parse(fp.read())

		# when added to a stixlangobj:
		o = stixlangwrap([ 'th', 'en' ], camp)
		o.addtranslationobject(transobj)

		# work as expected
		self.assertEqual(o.getlangtext('description'),
		    ('th', 'a Thai description'))

	def test_notfoundbundle(self):
		desc = 'This is a basic description of a campaign.'
		camp = Campaign(name='A Campaign', lang='en', description=desc,
		    created_by_ref=self.ident.id)

		o = stixlangwrap('en', camp)

		bundle = Bundle(objects=[ camp, _BogusLC(object_ref=camp.id) ])

		self.assertRaises(ValueError, o.addtranslationobject,
		    bundle=bundle)

	def test_granularmarkings(self):
		with open('test_granlang.json') as fp:
			campobj = stix2.parse(fp.read())

		o = stixlangwrap('en', campobj)

		self.assertRaises(AttributeError, o.getlangtext, 'description')

		o = stixlangwrap([ 'de', 'en' ], campobj)

		self.assertEqual(o.getlangtext('description'), ('de', u'Weitere Informationen über Banküberfall'))

	# Cannot fetch the lang marking with the stix2 library
	# https://github.com/oasis-open/cti-python-stix2/issues/251
	@unittest.skip('granular markings broken')
	def test_ctigranularmarkings(self):
		with open('test_granlang.json') as fp:
			campobj = stix2.parse(fp.read())

		campobj.get_markings('description')

	def test_granularnomarkings(self):
		with open('test_grannolang.json') as fp:
			campobj = stix2.parse(fp.read())

		o = stixlangwrap('en', campobj)

		self.assertEqual(o.getlangtext('description'), ('en', u'Weitere Informationen über Banküberfall'))
