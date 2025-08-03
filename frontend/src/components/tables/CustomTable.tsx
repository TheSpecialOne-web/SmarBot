import FilterListIcon from "@mui/icons-material/FilterList";
import {
  Box,
  Checkbox,
  FormControlLabel,
  IconButton,
  List,
  ListItem,
  Paper,
  Popover,
  Stack,
  styled,
  SxProps,
  Table,
  TableBody,
  TableCell,
  TableCellProps,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  Typography,
} from "@mui/material";
import { ChangeEvent, FormEvent, MouseEvent, ReactNode, useEffect, useRef, useState } from "react";
import { useEffectOnce } from "react-use";

import { theme } from "@/theme";

import { SearchField } from "../inputs/SearchField";
import { Spacer } from "../spacers/Spacer";

export type Order = "asc" | "desc";

export type CustomTableColumn<T> = {
  key: keyof T;
  label: ReactNode;
  align: "left" | "right" | "center";
  href?: string;
  maxWidth?: number;
  minWidth?: number;
  cellSx?: SxProps;
  render?: (item: T) => ReactNode;
  sortFunction?: (items: T[], order: Order, orderBy: keyof T) => T[];
  columnFilterProps?: {
    filterItems: {
      key: string;
      label: string;
    }[];
    filterFunction: (items: T[], queries: string[]) => T[];
  };
};

const getDefaultColumnFilters = <T extends { id: T["id"] }>(
  columns: CustomTableColumn<T>[],
): ColumnFilteredState<T> => {
  const defaultColumnFilters: ColumnFilteredState<T> = [];
  columns.forEach(column => {
    if (column?.columnFilterProps) {
      defaultColumnFilters.push({
        columnKey: column.key,
        filterKeys: column.columnFilterProps.filterItems.map(f => f.key),
      });
    }
  });
  return defaultColumnFilters;
};

type CheckboxProps<T extends { id: T["id"] }> = {
  selectedRowIds: T["id"][];
  setSelectedRowIds: (rowIds: T["id"][]) => void;
  isCheckable?: (row: T) => boolean;
};

type Props<T extends { id: T["id"] }> = {
  tableColumns: CustomTableColumn<T>[];
  tableData: T[];
  searchFilter?: (items: T[], query: string) => T[];
  defaultSortProps?: {
    key: keyof T;
    order: Order;
  };
  checkboxProps?: CheckboxProps<T>;
  noDataContent?: ReactNode;
  renderActionColumn?: (item: T) => ReactNode;
  maxTableHeight?: number;
  hideControlHeader?: boolean;
  hideTablePagination?: boolean;
  showRenderActionOnHover?: boolean;
};

type ColumnFilteredState<T> = {
  columnKey: keyof T;
  filterKeys: string[];
}[];

interface RenderActionColumnCellProps extends TableCellProps {
  hideBoxShadow?: boolean;
  showRenderActionOnHover?: boolean;
}

const RenderActionColumnCell = styled(TableCell, {
  shouldForwardProp: prop => !["hideBoxShadow", "showRenderActionOnHover"].includes(prop as string),
})<RenderActionColumnCellProps>(({ hideBoxShadow, showRenderActionOnHover }) => ({
  position: "sticky",
  right: 0,
  backgroundColor: "white",
  width: 50,
  opacity: showRenderActionOnHover ? 0 : 1,
  transition: "opacity 0.2s ease, box-shadow 0.3s ease",
  "tr:hover &": {
    opacity: 1,
  },
  ":before": {
    content: "''",
    display: "block",
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    boxShadow: hideBoxShadow ? "none" : `-4px 0 6px -1px ${theme.palette.boxShadow.main}`,
    transition: "box-shadow 0.3s ease",
  },
}));

export const CustomTable = <T extends { id: T["id"] }>({
  tableColumns,
  tableData,
  defaultSortProps = {
    key: "id",
    order: "asc",
  },
  searchFilter,
  checkboxProps: checkboxPropsArg,
  noDataContent,
  renderActionColumn,
  maxTableHeight,
  hideControlHeader = false,
  hideTablePagination = false,
  showRenderActionOnHover = false,
}: Props<T>) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hideBoxShadow, setHideBoxShadow] = useState(true);
  const [page, setPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [itemsPerPage, setItemsPerPage] = useState<number>(20);

  const [columnOrder, setColumnOrder] = useState<{
    key: keyof T;
    order: Order;
  }>(defaultSortProps);
  const [filterOpenStates, setFilterOpenStates] = useState<{ [key in keyof T]?: boolean }>({});

  const [filteredData, setFilteredData] = useState<T[]>(tableData);

  const defaultColumnFilters = getDefaultColumnFilters(tableColumns);
  const [columnFilters, setColumnFilters] = useState<ColumnFilteredState<T>>(defaultColumnFilters);

  const anchorEls = useRef<{ [key in keyof T]?: HTMLButtonElement | null }>({});

  const handleScroll = () => {
    if (paginatedData.length === 0) {
      setHideBoxShadow(true);
      return;
    }
    if (containerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth: containerWidth } = containerRef.current;
      const isScrolledToEnd = Math.abs(scrollWidth - containerWidth - scrollLeft) < 1;
      setHideBoxShadow(scrollWidth !== containerWidth ? isScrolledToEnd : true);
    }
  };

  useEffectOnce(() => {
    handleScroll();
  });

  const handleSort = (columnKey: keyof T) => {
    if (columnOrder.key === columnKey) {
      setColumnOrder(prevOrder => ({
        key: prevOrder.key,
        order: prevOrder.order === "asc" ? "desc" : "asc",
      }));
    } else {
      setColumnOrder({ key: columnKey, order: "asc" });
    }
  };

  const handleSearchChange = (event: FormEvent<HTMLInputElement>) => {
    setSearchQuery(event.currentTarget.value);
  };

  const handleToggleFilterCheck = (columnKey: keyof T, query: string) => {
    setColumnFilters(existingFilters => {
      // columnKey が existingFilters 配列に存在するか確認
      const isColumnKeyPresent = existingFilters.some(ef => ef.columnKey === columnKey);

      if (!isColumnKeyPresent) {
        return [...existingFilters, { columnKey, filterKeys: [query] }];
      }

      const newFilters = existingFilters.map(ef => {
        if (ef.columnKey !== columnKey) {
          return ef;
        }

        const updatedFilterKeys = ef.filterKeys.includes(query)
          ? ef.filterKeys.filter(t => t !== query) // query が存在する場合は削除
          : [...ef.filterKeys, query]; // 存在しない場合は追加

        return { ...ef, filterKeys: updatedFilterKeys };
      });
      return newFilters;
    });
  };

  const toggleFilterPopover = (columnKey: keyof T) => {
    setFilterOpenStates(prevStates => {
      return {
        ...prevStates,
        [columnKey]: !prevStates[columnKey],
      };
    });
  };

  useEffect(() => {
    let currentData = tableData;
    // 検索を適用
    if (searchFilter && searchQuery) {
      currentData = searchFilter(currentData, searchQuery);
    }

    // 列フィルターを適用
    columnFilters.forEach(filter => {
      const column = tableColumns.find(col => col.key === filter.columnKey);
      if (column?.columnFilterProps) {
        currentData = column.columnFilterProps.filterFunction(currentData, filter.filterKeys);
      }
    });

    // ソートを適用
    const sortableColumn = tableColumns.find(col => col.key === columnOrder.key);

    currentData = sortableColumn?.sortFunction
      ? sortableColumn.sortFunction(currentData, columnOrder.order, columnOrder.key)
      : currentData;

    setFilteredData(currentData);
  }, [
    searchQuery,
    columnFilters,
    tableData,
    searchFilter,
    tableColumns,
    columnOrder,
    itemsPerPage,
  ]);

  useEffect(() => {
    setPage(0);
  }, [searchQuery, columnFilters, columnOrder, itemsPerPage]);

  const paginatedData = hideTablePagination
    ? filteredData
    : filteredData.slice(page * itemsPerPage, (page + 1) * itemsPerPage);

  const checkboxProps: Required<CheckboxProps<T>> | null = checkboxPropsArg
    ? {
        ...checkboxPropsArg,
        isCheckable: (row: T) => {
          return checkboxPropsArg.isCheckable ? checkboxPropsArg.isCheckable(row) : true;
        },
      }
    : null;

  const checkIsAllSelected = (
    paginatedData: T[],
    checkboxProps: Required<CheckboxProps<T>> | null,
  ) => {
    if (!checkboxProps) {
      return false;
    }

    const checkableItems = paginatedData.filter(item => checkboxProps.isCheckable(item));
    const selectedRowIds = checkboxProps.selectedRowIds;

    if (checkableItems.length !== selectedRowIds.length) {
      return false;
    }

    return (
      checkableItems.length > 0 && checkableItems.every(item => selectedRowIds.includes(item.id))
    );
  };

  const isAllSelected = checkIsAllSelected(paginatedData, checkboxProps);

  const handleChangePage = (event: MouseEvent<HTMLButtonElement> | null, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setItemsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <>
      <Box>
        {!hideControlHeader && (
          <Paper
            sx={{
              backgroundColor: "tableBackground.main",
              px: 2,
              py: 1,
              borderRadius: 0,
              marginBottom: "-1px",
              borderTop: "none !important",
            }}
            variant="outlined"
          >
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <SearchField value={searchQuery} onChange={handleSearchChange} />
              {!hideTablePagination && (
                <TablePagination
                  labelRowsPerPage="ページごとの最大行数"
                  rowsPerPageOptions={[20, 50, 100]}
                  component="div"
                  count={filteredData.length}
                  page={page}
                  onPageChange={handleChangePage}
                  rowsPerPage={itemsPerPage}
                  onRowsPerPageChange={handleChangeRowsPerPage}
                />
              )}
            </Stack>
          </Paper>
        )}
        <TableContainer
          component={Paper}
          elevation={0}
          variant="outlined"
          sx={{
            borderRadius: hideControlHeader ? "4px" : "0 0 4px 4px",
            maxHeight: maxTableHeight,
          }}
          ref={containerRef}
          onScroll={handleScroll}
        >
          <Table
            sx={{ minWidth: 650, borderCollapse: "unset" }}
            size={checkboxProps ? "small" : "medium"}
          >
            <TableHead sx={{ position: "sticky", top: 0, zIndex: 2 }}>
              <TableRow>
                {checkboxProps && (
                  <TableCell
                    sx={{
                      width: 50,
                      px: 1,
                    }}
                  >
                    <Checkbox
                      size="small"
                      onChange={() => {
                        const rowIds = paginatedData
                          .filter(item => checkboxProps.isCheckable(item))
                          .map(item => item.id);
                        checkboxProps.setSelectedRowIds(
                          isAllSelected
                            ? checkboxProps.selectedRowIds.filter(id => !rowIds.includes(id))
                            : [...new Set([...checkboxProps.selectedRowIds, ...rowIds])],
                        );
                      }}
                      checked={isAllSelected}
                    />
                  </TableCell>
                )}
                {tableColumns.map(column => (
                  <TableCell
                    key={column.key as string}
                    align={column.align}
                    sx={{
                      fontSize: 14,
                      fontWeight: "bold",
                      minWidth: column.minWidth ? column.minWidth : 180,
                      bgcolor: hideControlHeader ? "tableBackground.main" : undefined,
                      whiteSpace: "nowrap",
                    }}
                  >
                    <Stack direction="row" alignItems="center" display="inline-flex">
                      {column.label}
                      {/* ソート */}
                      {column?.sortFunction && (
                        <TableSortLabel
                          active={columnOrder.key === column.key}
                          direction={columnOrder.key === column.key ? columnOrder.order : "asc"}
                          onClick={() => handleSort(column.key)}
                        />
                      )}
                      {/* フィルター */}
                      {column?.columnFilterProps && (
                        <>
                          <Spacer px={4} horizontal />
                          <IconButton
                            ref={(anchorEl: HTMLButtonElement) => {
                              anchorEls.current[column.key] = anchorEl;
                            }}
                            color="primary"
                            onClick={() => toggleFilterPopover(column.key)}
                            size="small"
                          >
                            <FilterListIcon />
                          </IconButton>
                        </>
                      )}
                      {/* フィルターの中身 */}
                      {filterOpenStates && (
                        <Popover
                          open={filterOpenStates[column.key] || false}
                          anchorEl={anchorEls.current[column.key]}
                          onClose={() => toggleFilterPopover(column.key)}
                        >
                          <List>
                            <Stack gap={1} py={1}>
                              {column.columnFilterProps?.filterItems.map(item => {
                                const checked = columnFilters.some(
                                  f =>
                                    f.columnKey === column.key && f.filterKeys.includes(item.key),
                                );
                                return (
                                  <ListItem key={item.key} sx={{ py: 0 }}>
                                    <FormControlLabel
                                      control={
                                        <Checkbox
                                          checked={checked}
                                          onChange={() =>
                                            handleToggleFilterCheck(column.key, item.key)
                                          }
                                          sx={{ py: 0 }}
                                        />
                                      }
                                      label={<Typography variant="body2">{item.label}</Typography>}
                                    />
                                  </ListItem>
                                );
                              })}
                            </Stack>
                          </List>
                        </Popover>
                      )}
                    </Stack>
                  </TableCell>
                ))}
                {/* アクションカラム用に列を合わせる */}
                {renderActionColumn && paginatedData.length != 0 && (
                  <RenderActionColumnCell
                    hideBoxShadow={true}
                    sx={{ bgcolor: hideControlHeader ? "tableBackground.main" : undefined }}
                  />
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedData.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={tableColumns.length + (checkboxProps ? 1 : 0)}
                    align="center"
                    sx={{
                      position: "relative",
                      height: "300px",
                    }}
                  >
                    {noDataContent || (
                      <Box
                        sx={{
                          position: "absolute",
                          top: "50%",
                          left: "50%",
                          transform: "translate(-50%, -50%)",
                        }}
                      >
                        <Typography variant="body2">データがありません。</Typography>
                      </Box>
                    )}
                  </TableCell>
                </TableRow>
              )}
              {paginatedData.map(data => {
                const isSelected = checkboxProps?.selectedRowIds.includes(data.id);
                return (
                  <TableRow
                    key={String(data.id)}
                    sx={{
                      maxHeight: 30,
                    }}
                  >
                    {checkboxProps && (
                      <TableCell
                        sx={{
                          width: 50,
                          px: 1,
                        }}
                      >
                        {checkboxProps.isCheckable(data) && (
                          <Checkbox
                            size="small"
                            onChange={() => {
                              checkboxProps.setSelectedRowIds(
                                isSelected
                                  ? checkboxProps.selectedRowIds.filter(id => id !== data.id)
                                  : [...new Set([...checkboxProps.selectedRowIds, data.id])],
                              );
                            }}
                            checked={isSelected}
                          />
                        )}
                      </TableCell>
                    )}
                    {tableColumns.map(col => (
                      <TableCell key={col.key as string} align={col.align} sx={col.cellSx}>
                        {col.render ? (
                          col.render(data)
                        ) : (
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: col.maxWidth ? col.maxWidth : 360,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {data[col.key] as unknown as string}
                          </Typography>
                        )}
                      </TableCell>
                    ))}
                    {renderActionColumn && (
                      <RenderActionColumnCell
                        showRenderActionOnHover={showRenderActionOnHover}
                        hideBoxShadow={renderActionColumn(data) === null ? true : hideBoxShadow}
                        sx={{
                          bgcolor: renderActionColumn(data) === null ? "transparent" : undefined,
                        }}
                      >
                        {renderActionColumn(data)}
                      </RenderActionColumnCell>
                    )}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </>
  );
};
