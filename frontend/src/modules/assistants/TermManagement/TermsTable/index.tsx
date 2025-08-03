import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { Box, IconButton, Stack, Typography } from "@mui/material";

import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { TermV2 } from "@/orval/models/backend-api";

const filterTerm = (terms: TermV2[], query: string) => {
  return terms.filter(term => {
    return filterTest(query, [term.description, ...term.names]);
  });
};

const sortTerms = (terms: TermV2[], order: Order, orderBy: keyof TermV2) => {
  const comparator = getComparator<TermV2>(order, orderBy);
  return [...terms].sort(comparator);
};

type Props = {
  hasWritePolicy: boolean;
  terms: TermV2[];
  isLoadingFetchTerms: boolean;
  selectedRowIds: string[];
  handleSelectRow: (selectedRowIds: string[]) => void;
  onClickUpdateIcon: (term: TermV2) => void;
};

export const TermsTable = ({
  hasWritePolicy,
  terms,
  isLoadingFetchTerms,
  selectedRowIds,
  handleSelectRow,
  onClickUpdateIcon,
}: Props) => {
  const noTermContent = hasWritePolicy && terms.length === 0 && (
    <Box
      sx={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      }}
    >
      <Typography variant="body2">
        右上の「追加」ボタンをクリックして用語を追加してください。
      </Typography>
    </Box>
  );

  const renderActionColumn = (term: TermV2) => {
    if (!hasWritePolicy) return null;
    return (
      <IconButton onClick={() => onClickUpdateIcon(term)}>
        <EditOutlinedIcon color="primary" />
      </IconButton>
    );
  };

  const tableColumns: CustomTableColumn<TermV2>[] = [
    {
      key: "names",
      label: "用語",
      align: "left",
      render: (row: TermV2) => (
        <Stack>
          {row.names.map(name => (
            <Typography key={name}>{name}</Typography>
          ))}
        </Stack>
      ),
    },
    {
      key: "description",
      label: "説明",
      align: "left",
      sortFunction: sortTerms,
    },
  ];

  return (
    <>
      {isLoadingFetchTerms ? (
        <CustomTableSkeleton />
      ) : (
        <CustomTable<TermV2>
          tableColumns={tableColumns}
          tableData={terms}
          noDataContent={noTermContent}
          searchFilter={filterTerm}
          renderActionColumn={renderActionColumn}
          checkboxProps={{
            selectedRowIds: selectedRowIds,
            setSelectedRowIds: handleSelectRow,
          }}
        />
      )}
    </>
  );
};
