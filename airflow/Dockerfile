FROM apache/airflow:2.9.3-python3.11

ENV PYTHONPATH=/opt/airflow

USER root

RUN apt-get update \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements ./requirements
RUN pip uninstall -y \
        apache-airflow-providers-google \
        apache-airflow-providers-amazon \
        apache-airflow-providers-microsoft-azure \
        apache-airflow-providers-slack \
        apache-airflow-providers-ssh \
        apache-airflow-providers-sftp \
        apache-airflow-providers-ftp \
        apache-airflow-providers-imap \
        apache-airflow-providers-mongo \
        apache-airflow-providers-redis \
        apache-airflow-providers-mysql \
        apache-airflow-providers-oracle \
        apache-airflow-providers-snowflake \
        apache-airflow-providers-databricks \
        apache-airflow-providers-elasticsearch \
        apache-airflow-providers-docker \
        apache-airflow-providers-kubernetes \
        apache-airflow-providers-celery \
        apache-airflow-providers-cncf-kubernetes \
        apache-airflow-providers-apache-spark \
        apache-airflow-providers-apache-hive \
        apache-airflow-providers-apache-kafka || true

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/etl.txt

COPY airflow/dags /opt/airflow/dags
COPY etl /opt/airflow/etl
