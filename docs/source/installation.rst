============
Installation
============

Prerequisites
=============

- **Python 3.11 or later** is required
- Install with `uv <https://docs.astral.sh/uv/>`_ (recommended) or with `pip`

With uv (recommended)
=====================

.. code-block:: bash

   uv pip install odr-bootstrap

   # or add it to a project managed with uv
   uv add odr-bootstrap

With pip
========

.. code-block:: bash

   pip install odr-bootstrap

From source
===========

.. code-block:: bash

   git clone https://github.com/whtowbin/odr_bootstrap_package.git
   cd odr_bootstrap_package

   # recommended development setup
   uv sync --all-extras

   # install the package in editable mode
   uv pip install -e .

   # or with pip
   pip install -e ".[dev,test,docs]"

Optional dependency groups
==========================

Install only the extras you need:

.. code-block:: bash

   uv pip install "odr-bootstrap[test]"
   uv pip install "odr-bootstrap[dev]"
   uv pip install "odr-bootstrap[docs]"
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
