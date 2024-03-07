"""Test the documentation info module."""

from os import chdir, getcwd
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.dev.doc.doc_info import (
    DocInfo,
    load_doc_info_from_setup_cfg,
    parse_readme_md,
    parse_version_py,
)
from pycommons.io.path import Path, file_path, write_lines
from pycommons.io.temp import temp_dir


def test_parse_readme_md() -> None:
    """Test parsing of readme.md files."""
    base: Final[Path] = file_path(__file__).up()

    try:
        parse_readme_md(base.resolve_inside("md_2_titles.md"))
    except ValueError as ve:
        assert str(ve).startswith("Already have title")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Got '## x. blubb' and finding index 1")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("Got '## blubb' after having index.")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_3.md"))
    except ValueError as ve:
        assert str(ve).startswith("Found index 1 in line '## 1. blubb'")
    else:
        pytest.fail("There should be an error!")
    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_4.md"))
    except ValueError as ve:
        assert str(ve).startswith("Got '## a. blubb' and finding index")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_no_title.md"))
    except ValueError as ve:
        assert str(ve).startswith("No title in '")
    else:
        pytest.fail("There should be an error!")


def test_parse_version() -> None:
    """Test parsing of version.py files."""
    base: Final[Path] = file_path(__file__).up()

    try:
        parse_version_py(base.resolve_inside(
            "version_error_1.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Incorrect string limits for")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_2.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Strange version string")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_2.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Strange version string")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_3.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Version defined as")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_4.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Undelimited string in")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_5.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Did not find version attr")
    else:
        pytest.fail("There should be an error!")


def test_load_doc_info_from_setup_cfg() -> None:
    """Test loading the documentation info."""
    doc_base: Final[Path] = file_path(__file__).up()
    pro_base: Final[Path] = doc_base.up(4)

    di: Final[DocInfo] = load_doc_info_from_setup_cfg(
        pro_base.resolve_inside("setup.cfg"))
    assert isinstance(di, DocInfo)
    assert di.project == "pycommons"
    assert di.readme_md_file == pro_base.resolve_inside("README.md")
    assert di.author == "Thomas Weise"
    assert str.__len__(di.title) > 10
    assert di.doc_url == "https://thomasweise.github.io/pycommons"
    v: list[str] = di.version.split(".")
    assert isinstance(v, list)
    assert list.__len__(v) == 3
    for vs in v:
        assert isinstance(vs, str)
        assert str.__len__(str.strip(vs)) > 0
        assert vs.isnumeric()

    cd: Final[str] = getcwd()

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_ok_1.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            di2 = load_doc_info_from_setup_cfg(f)
            assert isinstance(di2, DocInfo)
            assert di2.project == "pycommons"
            assert di2.readme_md_file == rdme
            assert di2.author == "Thomas Weise"
            assert str.__len__(di2.title) > 10
            assert di2.doc_url == \
                "https://thomasweise.github.io/pycommons"
            v: list[str] = di2.version.split(".")
            assert isinstance(v, list)
            assert list.__len__(v) == 3
            for vs in v:
                assert isinstance(vs, str)
                assert str.__len__(str.strip(vs)) > 0
                assert vs.isnumeric()
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_ok_2.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            di2 = load_doc_info_from_setup_cfg(f)
            assert isinstance(di2, DocInfo)
            assert di2.project == "pycommons"
            assert di2.readme_md_file == rdme
            assert di2.author == "Thomas Weise"
            assert str.__len__(di2.title) > 10
            assert di2.doc_url == \
                "https://thomasweise.github.io/pycommons"
            v: list[str] = di2.version.split(".")
            assert isinstance(v, list)
            assert list.__len__(v) == 3
            for vs in v:
                assert isinstance(vs, str)
                assert str.__len__(str.strip(vs)) > 0
                assert vs.isnumeric()
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_1.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            load_doc_info_from_setup_cfg(f)
        except ValueError as ve:
            assert str(ve).startswith("Invalid version attribute")
        else:
            pytest.fail("There should be an error!")

        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_1.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            load_doc_info_from_setup_cfg(f)
        except ValueError as ve:
            assert str(ve).startswith("Invalid version attribute")
        else:
            pytest.fail("There should be an error!")

        finally:
            chdir(cd)
    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_2.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            load_doc_info_from_setup_cfg(f)
        except ValueError as ve:
            assert str(ve).startswith("Invalid long_description attribute")
        else:
            pytest.fail("There should be an error!")

        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_3.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            load_doc_info_from_setup_cfg(f)
        except ValueError as ve:
            assert str(ve).startswith("long_description 'bla' does not point")
        else:
            pytest.fail("There should be an error!")

        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_4.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            load_doc_info_from_setup_cfg(f)
        except ValueError as ve:
            assert str(ve).startswith("Two docu URLs found?")
        else:
            pytest.fail("There should be an error!")

        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme: Path = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_5.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            load_doc_info_from_setup_cfg(f)
        except ValueError as ve:
            assert str(ve).startswith("Strange URL line")
        else:
            pytest.fail("There should be an error!")

        finally:
            chdir(cd)
