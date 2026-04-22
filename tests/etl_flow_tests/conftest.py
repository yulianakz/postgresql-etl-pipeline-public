"""Shared fixtures for ETL tests.

Airflow is a heavy, platform-sensitive dependency and the pieces of the
codebase we want to exercise only reference two symbols from it:

- ``airflow.exceptions.AirflowSkipException``

We install a minimal stub for that package *before* any ETL module is
imported so the tests can run in environments where Apache Airflow is
not installed (e.g. CI for unit tests).
"""

import sys
import types


def _install_airflow_stub() -> None:
    if "airflow" in sys.modules:
        return

    airflow = types.ModuleType("airflow")
    exceptions = types.ModuleType("airflow.exceptions")

    class AirflowSkipException(Exception):
        """Local stub mirroring :class:`airflow.exceptions.AirflowSkipException`."""

    exceptions.AirflowSkipException = AirflowSkipException
    airflow.exceptions = exceptions

    sys.modules["airflow"] = airflow
    sys.modules["airflow.exceptions"] = exceptions


_install_airflow_stub()
