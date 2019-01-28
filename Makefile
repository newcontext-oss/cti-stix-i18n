test:
	(echo stixi18n.py) | (. ./p/bin/activate && ~/src/eradman-entr-c15b0be493fc/entr sh -c 'python -m coverage run -m unittest stixi18n && python -m coverage report -m --omit=p/\*')

setupenv:
	virtualenv-2.7 p && \
	( . ./p/bin/activate && pip install -r requirements.txt)
