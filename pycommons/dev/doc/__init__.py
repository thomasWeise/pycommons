"""
Tools for making the documentation.

In all of my projects, the documentation is generated in the same way from
the same data. Therefore, this process is unified here, which makes it easier
to apply changes throughout all projects.

The general idea is that we take all the information from the `setup.cfg`,
`README.md`, and `version.py` files and use it to automatically fill the
parameters of sphinx and to construct `index.rst` and a variant of `README.md`
that the myst parser used by sphinx can properly render.
"""
