.. _development:

Development
===========

To install for development:

1. Fork the `webhook2lambda2sqs <https://github.com/jantman/webhook2lambda2sqs>`_ repository on GitHub
2. Create a new branch off of master in your fork.

.. code-block:: bash

    $ virtualenv webhook2lambda2sqs
    $ cd webhook2lambda2sqs && source bin/activate
    $ pip install -e git+git@github.com:YOURNAME/webhook2lambda2sqs.git@BRANCHNAME#egg=webhook2lambda2sqs
    $ cd src/webhook2lambda2sqs

The git clone you're now in will probably be checked out to a specific commit,
so you may want to ``git checkout BRANCHNAME``.

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)

Testing
-------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox -e <environment name>``

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Acceptance Tests
++++++++++++++++

These will actually spin up the entire system end-to-end, send some messages via
POST and GET, and test that they work. It *should* clean everything up when finished.

``tox -e acceptance``

Use ``export NO_TEARDOWN=true`` to prevent tear-down of the infrastructure. When you're ready to
destroy it, ``unset NO_TEARDOWN`` and run ``tox -e acceptance`` again.

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off master for that issue.
2. Run the ``acceptance`` tox environment locally.
3. Confirm that there are CHANGES.rst entries for all major changes.
4. Ensure that Travis tests passing in all environments.
5. Ensure that test coverage is no less than the last release (ideally, 100%).
6. Increment the version number in webhook2lambda2sqs/version.py and add version and release date to CHANGES.rst, then push to GitHub.
7. Confirm that README.rst renders correctly on GitHub.
8. Upload package to testpypi:

   * Make sure your ~/.pypirc file is correct (a repo called ``test`` for https://testpypi.python.org/pypi)
   * ``rm -Rf dist``
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist bdist_wheel``
   * ``twine upload -r test dist/*``
   * Check that the README renders at https://testpypi.python.org/pypi/webhook2lambda2sqs

9. Create a pull request for the release to be merged into master. Upon successful Travis build, merge it.
10. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -a vX.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin vX.Y.Z``

11. Upload package to live pypi:

    * ``twine upload dist/*``

12. make sure any GH issues fixed in the release were closed.
