"""Test the documentation info module."""

from os import chdir, getcwd
from re import compile as re_compile
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.dev.doc.doc_info import (
    DocInfo,
    extract_md_infos,
    load_doc_info_from_setup_cfg,
    parse_version_py,
)
from pycommons.io.path import Path, file_path, write_lines
from pycommons.io.temp import temp_dir


def test_extract_md_infos() -> None:
    """Test parsing of readme.md files."""
    base: Final[Path] = file_path(__file__).up()

    with pytest.raises(ValueError, match=re_compile(r"Already have title.*")):
        extract_md_infos(base.resolve_inside("md_2_titles.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Got '## x. blubb' and finding index 1.*")):
        extract_md_infos(base.resolve_inside(
            "md_error_2nd_level_heading_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Got '## blubb' after having index.*")):
        extract_md_infos(base.resolve_inside(
            "md_error_2nd_level_heading_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Found index 1 in line '## 1. blubb'.*")):
        extract_md_infos(base.resolve_inside(
            "md_error_2nd_level_heading_3.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Got '## a. blubb' and finding index.*")):
        extract_md_infos(base.resolve_inside(
            "md_error_2nd_level_heading_4.md"))

    with pytest.raises(ValueError, match=re_compile(r"No title in '.*")):
        extract_md_infos(base.resolve_inside(
            "md_error_no_title.md"))


def test_parse_version() -> None:
    """Test parsing of version.py files."""
    base: Final[Path] = file_path(__file__).up()

    with pytest.raises(
            ValueError, match=re_compile(r"Incorrect string limits for.*")):
        parse_version_py(base.resolve_inside(
            "version_error_1.txt"))

    with pytest.raises(ValueError, match=re_compile(
            r"Strange version string.*")):
        parse_version_py(base.resolve_inside(
            r"version_error_2.txt"))

    with pytest.raises(ValueError, match=re_compile(
            r"Strange version string.*")):
        parse_version_py(base.resolve_inside(
            r"version_error_2.txt"))

    with pytest.raises(ValueError, match=re_compile(
            r"Version defined as.*")):
        parse_version_py(base.resolve_inside(
            "version_error_3.txt"))

    with pytest.raises(ValueError, match=re_compile(
            r"Undelimited string in.*")):
        parse_version_py(base.resolve_inside(
            r"version_error_4.txt"))

    with pytest.raises(ValueError, match=re_compile(
            r"Did not find version attr.*")):
        parse_version_py(base.resolve_inside(
            "version_error_5.txt"))


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
            v = di2.version.split(".")
            assert isinstance(v, list)
            assert list.__len__(v) == 3
            for vs in v:
                assert isinstance(vs, str)
                assert str.__len__(str.strip(vs)) > 0
                assert vs.isnumeric()
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
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
            v = di2.version.split(".")
            assert isinstance(v, list)
            assert list.__len__(v) == 3
            for vs in v:
                assert isinstance(vs, str)
                assert str.__len__(str.strip(vs)) > 0
                assert vs.isnumeric()
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_1.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            with pytest.raises(
                    ValueError, match=re_compile(
                        r"Invalid version attribute.*")):
                load_doc_info_from_setup_cfg(f)
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_1.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            with pytest.raises(
                    ValueError, match=re_compile(
                        r"Invalid version attribute.*")):
                load_doc_info_from_setup_cfg(f)
        finally:
            chdir(cd)
    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_2.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            with pytest.raises(
                    ValueError, match=re_compile(
                        r"Invalid long_description attribute.*")):
                load_doc_info_from_setup_cfg(f)
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_3.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            with pytest.raises(
                    ValueError, match=re_compile(
                        r"long_description 'bla' does not point.*")):
                load_doc_info_from_setup_cfg(f)
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_4.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            with pytest.raises(ValueError, match=re_compile(
                    r"Two docu URLs found?.*")):
                load_doc_info_from_setup_cfg(f)
        finally:
            chdir(cd)

    with temp_dir() as td:
        rdme = td.resolve_inside("README.md")
        with rdme.open_for_write() as wd, \
                di.readme_md_file.open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        f = td.resolve_inside("setup.cfg")
        with f.open_for_write() as wd, \
                doc_base.resolve_inside(
                    "setup_cfg_error_5.txt").open_for_read() as rd:
            write_lines(rd.readlines(), wd)

        try:
            with pytest.raises(ValueError, match=re_compile(
                    r"Strange URL line.*")):
                load_doc_info_from_setup_cfg(f)
        finally:
            chdir(cd)
