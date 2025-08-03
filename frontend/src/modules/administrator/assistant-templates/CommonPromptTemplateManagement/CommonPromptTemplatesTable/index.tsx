import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { Box, IconButton, Typography } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { CommonPromptTemplate } from "@/orval/models/administrator-api";

const filterCommonPromptTemplate = (
  commonPromptTemplates: CommonPromptTemplate[],
  query: string,
) => {
  return commonPromptTemplates.filter(commonPromptTemplate => {
    return filterTest(query, [commonPromptTemplate.title, commonPromptTemplate.prompt]);
  });
};

// 質問例のソート
const sortCommonPromptTemplates = (
  promptTemplates: CommonPromptTemplate[],
  order: Order,
  orderBy: keyof CommonPromptTemplate,
) => {
  const comparator = getComparator<CommonPromptTemplate>(order, orderBy);
  return [...promptTemplates].sort(comparator);
};

const tableColumns: CustomTableColumn<CommonPromptTemplate>[] = [
  {
    key: "title",
    label: "タイトル",
    align: "left",
    sortFunction: sortCommonPromptTemplates,
  },
  {
    key: "prompt",
    label: "質問",
    align: "left",
    sortFunction: sortCommonPromptTemplates,
  },
];

type Props = {
  commonPromptTemplates: CommonPromptTemplate[];
  onClickUpdateIcon: (promptTemplate: CommonPromptTemplate) => void;
  selectedRowIds: string[];
  handleSelectRow: (rowIds: string[]) => void;
};

export const CommonPromptTemplatesTable = ({
  commonPromptTemplates,
  onClickUpdateIcon,
  selectedRowIds,
  handleSelectRow,
}: Props) => {
  const noCommonPromptTemplateContent = (
    <Box
      sx={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      }}
    >
      <Typography variant="body2">
        右上の「追加」ボタンをクリックして質問例を追加してください。
      </Typography>
    </Box>
  );

  const renderActionColumn = (pt: CommonPromptTemplate) => {
    return (
      <IconButton onClick={() => onClickUpdateIcon(pt)}>
        <EditOutlinedIcon color="primary" />
      </IconButton>
    );
  };

  return (
    <CustomTable<CommonPromptTemplate>
      tableColumns={tableColumns}
      tableData={commonPromptTemplates}
      noDataContent={noCommonPromptTemplateContent}
      searchFilter={filterCommonPromptTemplate}
      checkboxProps={{
        selectedRowIds: selectedRowIds,
        setSelectedRowIds: handleSelectRow,
      }}
      renderActionColumn={renderActionColumn}
    />
  );
};
