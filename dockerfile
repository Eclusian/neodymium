#
# dockerfile for python-neodymium.
# Build using the command:
#
# $ docker build . -t 'python-neodymium'
#
# Author: Kent Carrier | @embite | kentbo0528@gmail.com
#

FROM python:3.9

ADD .env .
ADD login.py .
ADD roles.txt .
ADD rules.txt .

RUN python -m pip install discord python-dotenv

CMD ["python", "login.py"]
