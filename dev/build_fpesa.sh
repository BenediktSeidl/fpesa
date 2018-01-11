set -exuva

python setup.py install
mv dev/fpesa.docker-compose.cfg fpesa.cfg
