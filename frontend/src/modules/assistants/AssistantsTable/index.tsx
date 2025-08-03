import dayjs from "dayjs";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { modelNames } from "@/const/modelFamily";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Bot } from "@/orval/models/backend-api";

import { AssistantsTableApproachColumn } from "../AssistantsTableApproachColumn";
import { AssistantsTableNameColumn } from "../AssistantsTableNameColumn";
import { AssistantsTableAction } from "./AssistantsTableAction";

const sortBots = (bots: Bot[], order: Order, orderBy: keyof Bot) => {
  const comparator = getComparator<Bot>(order, orderBy);
  return [...bots].sort(comparator);
};

const filterBot = (bots: Bot[], query: string) => {
  return bots.filter(bot => {
    return filterTest(query, [bot.name, bot.description]);
  });
};

const getTableColumns = (groupId?: number): CustomTableColumn<Bot>[] => [
  {
    key: "icon_url",
    label: "",
    align: "right",
    minWidth: 10,
    cellSx: { pr: 0.5 },
    render: bot => (
      <AssistantAvatar
        size={30}
        iconUrl={bot.icon_url}
        iconColor={bot.icon_color}
        sx={{ display: "inline-flex" }}
      />
    ),
  },
  {
    key: "name",
    label: "アシスタント名",
    align: "left",
    render: bot => <AssistantsTableNameColumn bot={bot} groupId={groupId} />,
    sortFunction: sortBots,
    minWidth: 300,
  },
  {
    key: "created_at",
    label: "作成日",
    align: "left",
    sortFunction: sortBots,
    render: bot => dayjs(bot.created_at).format("YYYY年M月D日"),
  },
  {
    key: "model_family",
    label: "モデル",
    align: "left",
    render: bot => modelNames[bot.model_family],
    sortFunction: sortBots,
  },
  {
    key: "approach",
    label: "ドキュメントの参照",
    align: "left",
    render: bot => <AssistantsTableApproachColumn bot={bot} />,
    sortFunction: sortBots,
    minWidth: 250,
  },
];

type Props = {
  bots: Bot[];
  groupId?: number;
  onClickStartChat: (bot: Bot) => void;
  onClickArchive: (bot: Bot) => void;
};

export const AssistantsTable = ({ bots, groupId, onClickStartChat, onClickArchive }: Props) => {
  const renderActionColumn = (bot: Bot) => {
    return (
      <AssistantsTableAction
        onClickStartChat={() => onClickStartChat(bot)}
        onClickArchive={() => onClickArchive(bot)}
        groupId={groupId}
      />
    );
  };

  return (
    <CustomTable<Bot>
      tableColumns={getTableColumns(groupId)}
      tableData={bots}
      searchFilter={filterBot}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
