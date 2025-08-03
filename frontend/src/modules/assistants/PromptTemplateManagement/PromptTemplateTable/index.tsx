import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { Box, IconButton, Typography } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { BotPromptTemplate } from "@/orval/models/backend-api";

const filterPromptTemplate = (promptTemplates: BotPromptTemplate[], query: string) => {
  return promptTemplates.filter(promptTemplate => {
    return filterTest(query, [
      promptTemplate.title,
      promptTemplate.description,
      promptTemplate.prompt,
    ]);
  });
};

// 質問例のソート
const sortPromptTemplates = (
  promptTemplates: BotPromptTemplate[],
  order: Order,
  orderBy: keyof BotPromptTemplate,
) => {
  const comparator = getComparator<BotPromptTemplate>(order, orderBy);
  return [...promptTemplates].sort(comparator);
};

const tableColumns: CustomTableColumn<BotPromptTemplate>[] = [
  {
    key: "title",
    label: "タイトル",
    align: "left",
    sortFunction: sortPromptTemplates,
  },
  {
    key: "prompt",
    label: "質問",
    align: "left",
    sortFunction: sortPromptTemplates,
  },
];

type Props = {
  promptTemplates: BotPromptTemplate[];
  onClickUpdateIcon: (promptTemplate: BotPromptTemplate) => void;
  selectedRowIds: string[];
  handleSelectRow: (rowIds: string[]) => void;
  hasWritePolicy: boolean;
};

export const PromptTemplatesTable = ({
  promptTemplates,
  onClickUpdateIcon,
  selectedRowIds,
  handleSelectRow,
  hasWritePolicy,
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
        {hasWritePolicy
          ? "右上の「追加」ボタンをクリックして質問例を追加してください。"
          : "質問例がありません。"}
      </Typography>
    </Box>
  );

  const renderActionColumn = (pt: BotPromptTemplate) => {
    if (!hasWritePolicy) {
      return null;
    }
    return (
      <IconButton onClick={() => onClickUpdateIcon(pt)}>
        <EditOutlinedIcon color="primary" />
      </IconButton>
    );
  };

  return (
    <CustomTable<BotPromptTemplate>
      tableColumns={tableColumns}
      tableData={promptTemplates}
      noDataContent={noPromptTemplateContent}
      searchFilter={filterPromptTemplate}
      checkboxProps={
        hasWritePolicy
          ? {
              selectedRowIds: selectedRowIds,
              setSelectedRowIds: handleSelectRow,
            }
          : undefined
      }
      renderActionColumn={renderActionColumn}
    />
  );
};
