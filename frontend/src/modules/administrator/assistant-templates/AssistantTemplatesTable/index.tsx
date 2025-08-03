import { Check } from "@mui/icons-material";
import CloseIcon from "@mui/icons-material/Close";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import { Icon, IconButton, Link, Stack } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterAssistantTemplatesByStatus } from "@/libs/columnFilter";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { BotTemplate } from "@/orval/models/administrator-api";
import { Approach } from "@/orval/models/backend-api";

const sortBots = (assistantTemplates: BotTemplate[], order: Order, orderBy: keyof BotTemplate) => {
  const comparator = getComparator<BotTemplate>(order, orderBy);
  return [...assistantTemplates].sort(comparator);
};

const filterBot = (assistantTemplates: BotTemplate[], query: string) => {
  return assistantTemplates.filter(assistantTemplate => {
    return filterTest(query, [assistantTemplate.name, assistantTemplate.description]);
  });
};

const tableColumns: CustomTableColumn<BotTemplate>[] = [
  {
    key: "icon_url",
    label: "",
    align: "right",
    minWidth: 10,
    cellSx: { pr: 0.5 },
    render: assistantTemplete => (
      <AssistantAvatar
        size={30}
        iconUrl={assistantTemplete.icon_url}
        iconColor={assistantTemplete.icon_color}
        sx={{ display: "inline-flex" }}
      />
    ),
  },
  {
    key: "name",
    label: "アシスタント名",
    align: "left",
    render: assistantTemplate => (
      <Link href={`#/administrator/assistant-templates/${assistantTemplate.id}`}>
        {assistantTemplate.name}
      </Link>
    ),
    sortFunction: sortBots,
  },
  {
    key: "description",
    label: "説明",
    align: "left",
    maxWidth: 300,
    sortFunction: sortBots,
  },
  {
    key: "model_family",
    label: "モデル",
    align: "left",
    render: assistantTemplate => assistantTemplate.model_family,
    sortFunction: sortBots,
  },
  {
    key: "is_public",
    label: "公開状況",
    align: "left",
    minWidth: 100,
    render: assistantTemplate => (
      <Stack direction="row" gap={1}>
        <Icon
          component={assistantTemplate.is_public ? Check : CloseIcon}
          color={assistantTemplate.is_public ? "success" : "error"}
        />
        <span>{assistantTemplate.is_public ? "公開" : "非公開"}</span>
      </Stack>
    ),
    columnFilterProps: {
      filterItems: [
        { key: "true", label: "公開" },
        { key: "false", label: "非公開" },
      ],
      filterFunction: filterAssistantTemplatesByStatus,
    },
  },
  {
    key: "approach",
    label: "ドキュメントの参照",
    align: "center",
    minWidth: 100,
    render: assistantTemplate =>
      assistantTemplate.approach == Approach.neollm ? (
        <Check color="success" />
      ) : (
        <CloseIcon color="error" />
      ),
    sortFunction: sortBots,
  },
];

type Props = {
  assistantTemplates: BotTemplate[];
  onClickDeleteIcon: (assistantTemplates: BotTemplate) => void;
};

export const AssistantTemplatesTable = ({ assistantTemplates, onClickDeleteIcon }: Props) => {
  const renderActionColumn = (assistantTemplate: BotTemplate) => {
    return (
      <IconButton onClick={() => onClickDeleteIcon(assistantTemplate)}>
        <DeleteOutlineOutlinedIcon color="error" />
      </IconButton>
    );
  };

  return (
    <CustomTable<BotTemplate>
      tableColumns={tableColumns}
      tableData={assistantTemplates}
      searchFilter={filterBot}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
