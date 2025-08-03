import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { Box, IconButton, Typography } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { PromptTemplate } from "@/orval/models/backend-api";

const filterPromptTemplate = (promptTemplates: PromptTemplate[], query: string) => {
  return promptTemplates.filter(promptTemplate => {
    return filterTest(query, [
      promptTemplate.title,
      promptTemplate.description,
      promptTemplate.prompt,
    ]);
  });
};

// プロンプトテンプレートのソート
const sortPromptTemplates = (
  promptTemplates: PromptTemplate[],
  order: Order,
  orderBy: keyof PromptTemplate,
) => {
  const comparator = getComparator<PromptTemplate>(order, orderBy);
  return [...promptTemplates].sort(comparator);
};

const tableColumns: CustomTableColumn<PromptTemplate>[] = [
  {
    key: "title",
    label: "タイトル",
    align: "left",
    sortFunction: sortPromptTemplates,
  },
  {
    key: "description",
    label: "説明",
    align: "left",
    sortFunction: sortPromptTemplates,
  },
  {
    key: "prompt",
    label: "プロンプト",
    align: "left",
    sortFunction: sortPromptTemplates,
  },
];

type Props = {
  promptTemplates: PromptTemplate[];
  onClickUpdateIcon: (promptTemplate: PromptTemplate) => void;
  selectedRowIds: number[];
  handleSelectRow: (ids: number[]) => void;
};

export const PromptTemplatesTable = ({
  promptTemplates,
  onClickUpdateIcon,
  selectedRowIds,
  handleSelectRow,
}: Props) => {
  const noPromptTemplateContent = (
    <Box
      sx={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      }}
    >
      <Typography variant="body2">
        右上の「追加」ボタンをクリックしてプロンプトテンプレートを追加してください。
      </Typography>
    </Box>
  );

  const renderActionColumn = (pt: PromptTemplate) => {
    return (
      <IconButton onClick={() => onClickUpdateIcon(pt)}>
        <EditOutlinedIcon color="primary" />
      </IconButton>
    );
  };

  return (
    <CustomTable<PromptTemplate>
      tableColumns={tableColumns}
      tableData={promptTemplates}
      noDataContent={noPromptTemplateContent}
      searchFilter={filterPromptTemplate}
      checkboxProps={{
        selectedRowIds: selectedRowIds,
        setSelectedRowIds: handleSelectRow,
      }}
      renderActionColumn={renderActionColumn}
    />
  );
};
