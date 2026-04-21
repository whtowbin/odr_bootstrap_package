============
Installation
============

Prerequisites
=============

- **Python 3.12 or later** is required
- Installing with `uv <https://github.com/astral-sh/uv>`_ (recommended) or `pip`

With uv (Recommended)
=====================

`uv <https://docs.astral.sh/uv/>`_ is a fast Python package manager written in Rust.

.. code-block:: bash

   # Install the package
   uv pip install odr-bootstrap

   # Or in a project with uv.toml
   uv add odr-bootstrap

With pip
========

Using the standard pip package manager:

.. code-block:: bash

   pip install odr-bootstrap

From Source
===========

For development or bleeding-edge usage:

.. code-block:: bash

   git clone https://github.com/whtowbin/odr-bootstrap.git
   cd odr-bootstrap

   # With uv (recommended)
   uv sync --all-extras
   uv pip install -e .

   # Or with pip
   pip install -e ".[dev,test,docs]"

Optional Dependencies
=====================

Additional dependencies for development:

**Testing & Coverage**

.. code-block:: bash

   uv pip install "odr-bootstrap[test]"

**Full Development Setup** (includes testing, linting, type checking)

.. code-block:: bash

   uv pip install "odr-bootstrap[dev]"

**Documentation** (for building docs locally)

.. code-block:: bash

   uv pip install "odr-bootstrap[docs]"

**All Extras**

.. code-block:: bash

   uv pip install "odr-bootstrap[dev,test,docs]"

Verify Installation
===================

Check that the package is installed correctly:

.. code-block:: python

   >>> import odr_bootstrap
   >>> odr_bootstrap.__version__
   '0.1.0'
   >>> from odr_bootstrap import ODR_Bootstrap
   >>> print(ODR_Bootstrap.__doc__)

Or from the command line:

.. code-block:: bash

   python -c "import odr_bootstrap; print(odr_bootstrap.__version__)"

Next Steps
==========

- Read the :doc:`tutorial` for a guided introduction
- Check out :doc:`examples` for complete working code
- Browse the :doc:`api` for detailed function documentation
