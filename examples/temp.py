"""An example for using temporary files and directories."""

from pycommons.io.temp import temp_dir, temp_file

with temp_dir() as td:
    print(f"This is a temporary directory: {td!r}.")
    print("It is created via temp_dir(), its path is stored in 'td', and it"
          " is deleted (with all of its contents inside) once the "
          "'with'-block ends.")

with temp_file() as tf:
    print(f"This is a temporary file: {tf!r}.")
    print("It is created via temp_file(), its path is stored in 'tf', and it "
          "is deleted automatically once the 'with'-block ends.")

with temp_dir() as td, temp_file(td) as tf:
    print(f"You can also create a temp file {tf!r} inside any directory, even "
          f"a temp directory {td!r} and have them deleted once your are done.")
