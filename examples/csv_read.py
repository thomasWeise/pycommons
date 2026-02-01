"""An example of CSV readers."""

from pycommons.io.csv import CsvReader


class Reader(CsvReader):
    """
    A little parser that creates dictionaries of rows.

    You can, of course, return arbitrary datastructures in
    method `parse_row`.
    """

    def __init__(self, columns: dict[str, int]) -> None:
        """
        Create the csv reader.

        :param columns: the column name + column index pairs
        """
        super().__init__(columns)
        self.cols = columns

    def parse_row(self, data: list[str]) -> dict:
        """
        Parse one row of data.

        :param row: the list of column values for the current row
        :returns: the data structured generated to represent the row;
            here: a simple dictionary
        """
        return {x: data[y] for x, y in self.cols.items()}


# Let's test this with some data.
text = ["a;b;c;d", "# test comment", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
        "", "10", "# 11;12"]

# Iterate over the data produced from CSV.
for p in Reader.read(text):
    print(p)
