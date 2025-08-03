import {
  Box,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

type Props = {
  rowsCount?: number;
  columnsCount?: number;
};

export const CustomTableSkeleton = ({ rowsCount = 5, columnsCount = 5 }: Props) => {
  return (
    <>
      <Paper
        sx={{
          backgroundColor: "tableBackground.main",
          padding: 1,
          borderRadius: 0,
          marginBottom: "-1px",
          borderTop: "none !important",
        }}
        variant="outlined"
      >
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <Box flexGrow={1}>
            {/* SearchBarのスケルトン */}
            <Skeleton
              animation="pulse"
              variant="rectangular"
              height={40}
              width={200}
              sx={{ flexGrow: 1 }}
            />
          </Box>
          {/* TablePaginationのスケルトン */}
          <Skeleton animation="pulse" variant="rectangular" width={200} height={52} />
        </Box>
      </Paper>
      <TableContainer
        component={Paper}
        elevation={0}
        variant="outlined"
        sx={{
          borderRadius: "0 0 4px 4px",
        }}
      >
        <Table sx={{ minWidth: 650 }}>
          {/* テーブルヘッダーのスケルトン */}
          <TableHead>
            <TableRow>
              {Array.from(new Array(columnsCount)).map((_, index) => (
                <TableCell key={index}>
                  <Skeleton animation="pulse" variant="text" width="100%" />
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          {/* テーブルボディのスケルトン */}
          <TableBody>
            {Array.from(new Array(rowsCount)).map((_, rowIndex) => (
              <TableRow
                key={rowIndex}
                sx={{
                  maxHeight: 30,
                }}
              >
                {Array.from(new Array(columnsCount)).map((_, cellIndex) => (
                  <TableCell key={cellIndex}>
                    <Skeleton animation="pulse" variant="text" width="100%" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};
