# Base from odoo official image 
FROM odoo:17.0
# Copy requirements file into the container. Could be also mount.
COPY requirements.in /requirements.in
# Install other addons from requirements
RUN pip install -r /requirements.in
# Copy script which initialize the database (odoo -i)
COPY ./container/entrypoint-dbbase /entrypoint-dbbase
