# the default goal is build
.DEFAULT_GOAL := build

# Set the shell to bash
SHELL := /bin/bash

# Get the location of the Python package binaries.
PYTHON_PACKAGE_BINARIES := $(shell python3 -m site --user-base)/bin

# Get the current working directory
CWD := $(shell pwd)

# Get the pycommons version.
VERSION := $(shell (less '$(CWD)/pycommons/version.py' | sed -n 's/__version__.*=\s*"\(.*\)"/\1/p'))

# Get the current date and time
NOW = $(shell date +'%0Y-%0m-%0d %0R:%0S')

# Print the status information.
status:
	echo "$(NOW): working directory: '$(CWD)'." &&\
	echo "$(NOW): pycommons version to build: '$(VERSION)'." &&\
	echo "$(NOW): python package binaries: '$(PYTHON_PACKAGE_BINARIES)'." &&\
	echo "$(NOW): shell: '$(SHELL)'"

# Cleaning means that the package is uninstalled if it is installed.
# Also, all build artifacts are deleted (as they will be later re-created).
clean: status
	echo "$(NOW): Cleaning up by first uninstalling pycommons (if installed) and then deleting all auto-generated stuff." && \
	pip uninstall -y pycommons || true && \
	echo "$(NOW): pycommons is no longer installed; now deleting auto-generated stuff." && \
	rm -rf *.whl && \
	find -type d -name "__pycache__" -prune -exec rm -rf {} \; &&\
	rm -rf .mypy_cache &&\
	rm -rf .ruff_cache &&\
	rm -rf .pytest_cache && \
	rm -rf build && \
	rm -rf dist && \
	rm -rf docs/build && \
	rm -rf docs/source/*.rst && \
	rm -rf pycommons.egg-info && \
	echo "$(NOW): Done cleaning up, pycommons is uninstalled and auto-generated stuff is deleted."

# Initialization: Install all requirements, both for executing the library and for the tests.
init: clean
	echo "$(NOW): Initialization: first install required packages from requirements.txt." && \
	pip install --no-input --timeout 360 --retries 100 -r requirements.txt && ## nosem \
	echo "$(NOW): Finished installing required packages from requirements.txt, now installing packages required for development from requirements-dev.txt." && \
	pip install --no-input --timeout 360 --retries 100 -r requirements-dev.txt && ## nosem \
	echo "$(NOW): Finished installing requirements from requirements-dev.txt, now printing all installed packages." &&\
	pip freeze &&\
	echo "$(NOW): Finished printing all installed packages."


# Run the unit tests.
test: init
	echo "$(NOW): Erasing old coverage data." &&\
	coverage erase &&\
	export PYTHONPATH=".:${PYTHONPATH}" &&\
	echo "$(NOW): Running pytest with doctests." &&\
	timeout --kill-after=15s 90m coverage run -a --include="pycommons/*" -m pytest --strict-config --doctest-modules --ignore=tests --ignore=examples &&\
	echo "$(NOW): Running pytest tests." &&\
	timeout --kill-after=15s 90m coverage run -a --include="pycommons/*" -m pytest --strict-config tests --ignore=examples &&\
	echo "$(NOW): Finished running pytest tests."

# Perform static code analysis.
static_analysis: init
	echo "$(NOW): Now performing static analysis." &&\
	export PYTHONPATH=".:${PYTHONPATH}" &&\
	python3 -m pycommons.dev.building.static_analysis --package pycommons &&\
	echo "$(NOW): Done: All static checks passed."

# We use sphinx to generate the documentation.
# This automatically checks the docstrings and such and such.
create_documentation: static_analysis test
	echo "$(NOW): Now building documentation." &&\
	export PYTHONPATH=".:${PYTHONPATH}" &&\
	python3 -m pycommons.dev.building.make_documentation --root . --package pycommons &&\
	echo "$(NOW): Done building documentation."

# Create different distribution formats, also to check if there is any error.
create_distribution: static_analysis test create_documentation
	echo "$(NOW): Now building source distribution file." &&\
	python3 setup.py check &&\
	python3 -m build &&\
	echo "$(NOW): Done with the build process, now checking result." &&\
	python3 -m twine check dist/* &&\
	echo "$(NOW): Now testing the tar.gz." &&\
	export tempDir=`mktemp -d` &&\
	echo "$(NOW): Created temp directory '$$tempDir'. Creating virtual environment." &&\
	python3 -m venv "$$tempDir" &&\
	echo "$(NOW): Created virtual environment, now activating it." &&\
	source "$$tempDir/bin/activate" &&\
	echo "$(NOW): Now installing tar.gz." &&\
	python3 -m pip --no-input --timeout 360 --retries 100 --require-virtualenv install "$(CWD)/dist/pycommons-$(VERSION).tar.gz" && ## nosem \
	echo "$(NOW): Installing tar.gz has worked. We now create the list of packages in this environment via pip freeze." &&\
	pip freeze > "$(CWD)/dist/pycommons-$(VERSION)-requirements_frozen.txt" &&\
	echo "$(NOW): Now fixing pycommons line in requirements file." &&\
	sed -i "s/^pycommons.*/pycommons==$(VERSION)/" "$(CWD)/dist/pycommons-$(VERSION)-requirements_frozen.txt" &&\
	echo "$(NOW): Now we deactivate the environment." &&\
	deactivate &&\
	rm -rf "$$tempDir" &&\
	echo "$(NOW): Now testing the wheel." &&\
	export tempDir=`mktemp -d` &&\
	echo "$(NOW): Created temp directory '$$tempDir'. Creating virtual environment." &&\
	python3 -m venv "$$tempDir" &&\
	echo "$(NOW): Created virtual environment, now activating it." &&\
	source "$$tempDir/bin/activate" &&\
	echo "$(NOW): Now installing wheel." &&\
	python3 -m pip --no-input --timeout 360 --retries 100 --require-virtualenv install "$(CWD)/dist/pycommons-$(VERSION)-py3-none-any.whl" && ## nosem \
	echo "$(NOW): Now we deactivate the environment." &&\
	deactivate &&\
	echo "$(NOW): Finished, cleaning up." &&\
	rm -rf "$$tempDir" &&\
	echo "$(NOW): Now also packaging the documentation." &&\
	cd docs/build &&\
	tar --dereference --exclude=".nojekyll" -c * | xz -v -9e -c > "$(CWD)/dist/pycommons-$(VERSION)-documentation.tar.xz" &&\
	cd $(CWD) &&\
	echo "$(NOW): Successfully finished building source distribution."

# We install the package and see if that works out.
install: create_distribution
	echo "$(NOW): Now installing pycommons." && \
	pip --no-input --timeout 360 --retries 100 -v install . && \
	echo "$(NOW): Successfully installed pycommons."

# The meta-goal for a full build
build: status clean init test static_analysis create_documentation create_distribution install
	echo "$(NOW): The build has completed."

# .PHONY means that the targets init and test are not associated with files.
# see https://stackoverflow.com/questions/2145590
.PHONY: build clean create_distribution create_documentation init install static_analysis status test
