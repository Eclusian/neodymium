#
# dockerfile for python-neodymium.
# Author: Kent Carrier | @embite | kentbo0528@gmail.com
#

FROM python:3.9

ADD .env .
ADD login.py .

RUN python -m pip install discord python-dotenv

CMD ["python", "login.py"]
