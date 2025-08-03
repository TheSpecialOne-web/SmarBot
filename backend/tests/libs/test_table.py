from api.libs.table import ChildCell, ParentCell, Table


class Test_Table:
    def dummy_single_cell(self) -> ParentCell:
        return ParentCell(
            text="dummy text",
        )

    def dummy_3_3_cell(self) -> ParentCell:
        return ParentCell(
            row_span=3,
            col_span=3,
        )

    def test_drop_rows_and_cols(self):
        table = Table(
            matrix=[
                [ParentCell(), ParentCell(), ParentCell()],
                [ParentCell(), self.dummy_single_cell(), ParentCell()],
                [ParentCell(), ParentCell(), ParentCell()],
            ]
        )
        table.drop_blank_rows_and_cols()
        assert table.matrix == [[self.dummy_single_cell()]]

    def test_drop_rows_and_cols_2(self):
        table = Table(
            matrix=[
                [
                    ParentCell(row_span=3, col_span=3),
                    ChildCell(parent_coord=(0, 0)),
                    ChildCell(parent_coord=(0, 0)),
                    ParentCell(),
                ],
                [
                    ChildCell(parent_coord=(0, 0)),
                    ChildCell(parent_coord=(0, 0)),
                    ChildCell(parent_coord=(0, 0)),
                    self.dummy_single_cell(),
                ],
                [
                    ChildCell(parent_coord=(0, 0)),
                    ChildCell(parent_coord=(0, 0)),
                    ChildCell(parent_coord=(0, 0)),
                    self.dummy_single_cell(),
                ],
                [ParentCell(), self.dummy_single_cell(), self.dummy_single_cell(), ParentCell()],
            ]
        )
        table.drop_blank_rows_and_cols()
        assert table.matrix == [
            [ParentCell(row_span=2, col_span=2), ChildCell(parent_coord=(0, 0)), self.dummy_single_cell()],
            [ChildCell(parent_coord=(0, 0)), ChildCell(parent_coord=(0, 0)), self.dummy_single_cell()],
            [self.dummy_single_cell(), self.dummy_single_cell(), ParentCell()],
        ]

    def test_drop_rows_and_cols_3(self):
        table = Table(
            matrix=[
                [
                    ParentCell(row_span=2, col_span=2),
                    ChildCell(parent_coord=(0, 0)),
                    ParentCell(),
                    ParentCell(),
                ],
                [
                    ChildCell(parent_coord=(0, 0)),
                    ChildCell(parent_coord=(0, 0)),
                    self.dummy_single_cell(),
                    self.dummy_single_cell(),
                ],
                [
                    ParentCell(),
                    self.dummy_single_cell(),
                    ParentCell(row_span=2, col_span=2),
                    ChildCell(parent_coord=(2, 2)),
                ],
                [
                    ParentCell(),
                    self.dummy_single_cell(),
                    ChildCell(parent_coord=(2, 2)),
                    ChildCell(parent_coord=(2, 2)),
                ],
            ]
        )
        table.drop_blank_rows_and_cols()
        assert table.matrix == [
            [ParentCell(), self.dummy_single_cell(), self.dummy_single_cell()],
            [self.dummy_single_cell(), ParentCell(row_span=2, col_span=2), ChildCell(parent_coord=(1, 1))],
            [self.dummy_single_cell(), ChildCell(parent_coord=(1, 1)), ChildCell(parent_coord=(1, 1))],
        ]

    def test_clean_up_text(self):
        table = Table(
            matrix=[
                [ParentCell(text="a:selected:")],
                [ParentCell(text="b:unselected:")],
            ]
        )
        assert table.matrix == [
            [ParentCell(text="a")],
            [ParentCell(text="b")],
        ]

    def test_to_chunk(self):
        table = Table(
            matrix=[
                [ParentCell(text="a", row_span=2), ParentCell(text="b")],
                [ChildCell(parent_coord=(0, 0)), ParentCell(text="c")],
            ]
        )
        row_1 = Table(matrix=[[ParentCell(text="a"), ParentCell(text="b")]])
        row_2 = Table(matrix=[[ParentCell(text="a"), ParentCell(text="c")]])
        assert table.to_chunks(table_chunk_size=1) == [row_1._to_md(), row_2._to_md()]

    def test_to_chunk_2(self):
        table = Table(
            matrix=[
                [ParentCell(text="a", row_span=2), ParentCell(text="b", col_span=2), ChildCell(parent_coord=(0, 1))],
                [ChildCell(parent_coord=(0, 0)), ParentCell(text="c"), ParentCell(text="d")],
            ]
        )
        row_1 = Table(matrix=[[ParentCell(text="a"), ParentCell(text="b")]])
        row_2 = Table(matrix=[[ParentCell(text="a"), ParentCell(text="c"), ParentCell(text="d")]])
        assert table.to_chunks(table_chunk_size=1) == [row_1._to_md(), row_2._to_md()]

    def test_to_chunk_3(self):
        table = Table(
            matrix=[
                [ParentCell(text="a", row_span=2), ParentCell(text="b", col_span=2), ChildCell(parent_coord=(0, 1))],
                [ChildCell(parent_coord=(0, 0)), ParentCell(text="c"), ParentCell(text="d")],
            ]
        )
        assert table.to_chunks(table_chunk_size=1000) == [table._to_html()]
