from stixi18n import *

import stix2

if __name__ == '__main__':
	with open('fixture_usecase2.json') as fp:
		bundle = stix2.parse(fp.read())

	report = [ x for x in bundle.objects if x.id ==
	    'report--f26964ea-5a35-4baa-8fb4-31edded1cbd2' ][0]

	reporttrans = stixlangwrap(['ja', 'en'], report)

	print 'name language:', reporttrans.getlangtext('name')[0]
	print 'description language:', reporttrans.getlangtext('description')[0]
