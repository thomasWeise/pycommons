"""An example of CSV writers."""

from typing import Iterable

from pycommons.io.csv import CsvWriter


class Writer(CsvWriter):
    """A little CSV writer that turns dictionaries into CSV rows."""

    def __init__(self, data: Iterable[dict[str, int]],
                 scope: str | None = None) -> None:
        """
        Create the writer for an `Iterable` of data.

        :param data: in this case, the data items are dictionaries mapping
            integers to strings, but they could also be other things
        :param scope: an optional column name prefix
        """
        super().__init__(data, scope)
        self.rows = sorted({dkey for datarow in data
                            for dkey in datarow})

    def get_column_titles(self) -> Iterable[str]:
        """Get the column titles."""
        return self.rows

    def get_row(self, data: dict[str, int]) -> Iterable[str]:
        """Turn a data item into a string iterable with the column data."""
        return map(str, (data.get(key, "") for key in self.rows))

    def get_header_comments(self) -> list[str]:
        """Get comments to be printed at the head."""
        return ["This is a header comment.", " We have two of it. "]

    def get_footer_comments(self) -> list[str]:
        """Get comments for the foot of the document."""
        return [" This is a footer comment."]


# The raw data: Dictionaries to be turned into CSV data.
dd = [{"a": 1, "c": 2}, {"b": 6, "c": 8},
      {"a": 4, "d": 12, "b": 3}, {}]

# Iterate over the produced CSV data and print it.
for p in Writer.write(dd):
    print(p)
