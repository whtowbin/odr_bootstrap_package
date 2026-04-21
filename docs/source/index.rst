===============================
ODR Bootstrap Documentation
===============================

**Orthogonal Distance Regression with Bootstrap Resampling for SIMS Calibration**

|tests| |coverage| |pypi| |license|

.. |tests| image:: https://github.com/whtowbin/odr-bootstrap/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/whtowbin/odr-bootstrap/actions/workflows/tests.yml

.. |coverage| image:: https://codecov.io/gh/whtowbin/odr-bootstrap/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/whtowbin/odr-bootstrap

.. |pypi| image:: https://img.shields.io/pypi/v/odr-bootstrap.svg
   :target: https://pypi.org/project/odr-bootstrap/

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT

What is ODR Bootstrap?
======================

When fitting calibration curves to scientific data, measurement errors exist in both the 
independent variable (x, e.g., concentration) and dependent variable (y, e.g., ion intensity). 
Ordinary least squares regression assumes errors only in y, leading to biased fits.

**Orthogonal Distance Regression (ODR)** properly accounts for uncertainties in both x and y. 
**Bootstrap resampling** estimates confidence intervals by repeatedly refitting the model to 
random subsamples of the calibration data.

This package combines these techniques for publication-ready uncertainty quantification in 
`SIMS <https://en.wikipedia.org/wiki/Secondary_ion_mass_spectrometry>`_ (Secondary Ion Mass 
Spectrometry) calibration analysis.

Features
========

✅ NumPy-style documentation for all functions  
✅ Type hints for complete IDE support  
✅ 22 comprehensive unit tests (100% pass rate, 97.6% coverage)  
✅ Runnable example workflow with synthetic data  
✅ Compatible with scipy 1.15+ (deprecated API updates handled)  
✅ Zero-intercept fits with proper parameter handling  
✅ Publication-ready calibration plots  
✅ Continuous integration & automated testing  

Getting Started
===============

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   tutorial
   examples

API Reference
=============

.. toctree::
   :maxdepth: 2
   :caption: API

   api

Development
===========

.. toctree::
   :maxdepth: 1
   :caption: Contributing & Support

   CONTRIBUTING
   changelog

Project Links
=============

- **Source Code**: `GitHub <https://github.com/whtowbin/odr-bootstrap>`_
- **Issue Tracker**: `GitHub Issues <https://github.com/whtowbin/odr-bootstrap/issues>`_
- **PyPI**: `odr-bootstrap <https://pypi.org/project/odr-bootstrap/>`_

License
=======

MIT License - See `LICENSE <https://github.com/whtowbin/odr-bootstrap/blob/main/LICENSE>`_ for details.

Citation
========

If you use this package in research, please cite:

.. code-block:: bibtex

   @software{towbin2025odr,
     title={ODR Bootstrap: Orthogonal Distance Regression with Bootstrap Resampling},
     author={Towbin, Henry},
     year={2025},
     url={https://github.com/whtowbin/odr-bootstrap}
   }

---

**Version**: |release| | **Last Updated**: April 2025
