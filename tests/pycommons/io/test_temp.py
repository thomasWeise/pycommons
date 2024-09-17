"""Test the temporary files and directories."""
from os.path import basename, dirname, exists, getsize, isdir, isfile, join

from pycommons.io.path import Path
from pycommons.io.temp import temp_dir, temp_file


def test_temp_file() -> None:
    """Test the creation and deletion of temporary files."""
    with temp_file() as pathstr:
        assert isinstance(pathstr, str)
        assert len(pathstr) > 0
        assert isfile(pathstr)
        assert exists(pathstr)
    assert not isfile(pathstr)
    assert not exists(pathstr)

    with temp_file(prefix="aaaa", suffix=".xxx") as pathstr:
        assert isinstance(pathstr, str)
        assert len(pathstr) > 0
        assert isfile(pathstr)
        assert exists(pathstr)
        bn = basename(pathstr)
        assert bn.startswith("aaaa")
        assert bn.endswith(".xxx")
    assert not isfile(pathstr)
    assert not exists(pathstr)


def test_temp_dir() -> None:
    """Test the creation and deletion of temporary directories."""
    with temp_dir() as pathstr:
        assert isinstance(pathstr, str)
        assert len(pathstr) > 0
        assert isdir(pathstr)
        assert exists(pathstr)
    assert not isdir(pathstr)
    assert not exists(pathstr)

    with temp_dir() as pathstr:
        assert isinstance(pathstr, str)
        assert len(pathstr) > 0
        assert isdir(pathstr)
        assert exists(pathstr)
        with temp_file(pathstr) as path2:
            assert isinstance(path2, str)
            assert dirname(path2) == pathstr
            assert len(path2) > 0
            assert isfile(path2)
            assert exists(path2)
        with temp_file(pathstr) as path2:
            assert isinstance(path2, str)
            assert dirname(path2) == pathstr
            assert len(path2) > 0
            assert isfile(path2)
            assert exists(path2)
        inner = join(pathstr, "xx.y")
        with open(inner, "w", encoding="utf8") as _:
            pass
        assert isfile(inner)
        assert exists(inner)
    assert not isdir(pathstr)
    assert not exists(pathstr)
    assert not exists(path2)
    assert not exists(inner)


def test_file_write() -> None:
    """Test creation the writing into a file."""
    with temp_dir() as tds:
        s = Path(join(tds, "a.txt"))
        assert isinstance(s, str)
        assert len(s) > 0
        assert s.startswith(tds)
        assert s.endswith("a.txt")
        assert not exists(s)
        s.write_all_str("xx")
        assert exists(s)
        assert isfile(s)
        assert getsize(s) > 0


def test_file_ensure_exists() -> None:
    """Test ensuring that a file exists."""
    with temp_dir() as tds:
        s = Path(join(tds, "a.txt"))
        assert isinstance(s, str)
        assert len(s) > 0
        assert s.startswith(tds)
        assert s.endswith("a.txt")
        assert not exists(s)
        existed = s.ensure_file_exists()
        assert isinstance(s, str)
        assert len(s) > 0
        assert s.startswith(tds)
        assert s.endswith("a.txt")
        assert exists(s)
        assert isfile(s)
        assert getsize(s) == 0
        assert not existed

        s.write_all_str("blablabla")

        old_size = getsize(s)
        assert old_size > 0

        existed = s.ensure_file_exists()
        assert exists(s)
        assert isfile(s)
        assert existed
