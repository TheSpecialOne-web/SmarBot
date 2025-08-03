import dayjs from "dayjs";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { modelNames } from "@/const/modelFamily";
import { formatBotStatus } from "@/libs/bot";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { BotWithGroup } from "@/orval/models/backend-api";

import { AssistantsTableApproachColumn } from "../AssistantsTableApproachColumn";
import { AssistantsTableNameColumn } from "../AssistantsTableNameColumn";
import { ArchivedAssistantsWithGroupTableAction } from "./ArchivedAssistantsWithGroupTableAction";

const sortBots = (bots: BotWithGroup[], order: Order, orderBy: keyof BotWithGroup) => {
  const comparator = getComparator<BotWithGroup>(order, orderBy);
  return [...bots].sort(comparator);
};

const filterBot = (bots: BotWithGroup[], query: string) => {
  return bots.filter(bot => {
    return filterTest(query, [bot.name, bot.description]);
  });
};

const tableColumns: CustomTableColumn<BotWithGroup>[] = [
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
    render: bot => <AssistantsTableNameColumn bot={bot} />,
    sortFunction: sortBots,
    minWidth: 300,
  },
  {
    key: "group_name",
    label: "グループ名",
    align: "left",
    sortFunction: sortBots,
    minWidth: 250,
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
    sortFunction: sortBots,
    render: bot => modelNames[bot.model_family],
  },
  {
    key: "status",
    label: "ステータス",
    align: "left",
    render: bot => formatBotStatus(bot.status),
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
  bots: BotWithGroup[];
  onClickRestore: (bot: BotWithGroup) => void;
  onClickDelete: (bot: BotWithGroup) => void;
};

export const ArchivedAssistantsWithGroupTable = ({
  bots,
  onClickRestore,
  onClickDelete,
}: Props) => {
  const renderActionColumn = (bot: BotWithGroup) => (
    <ArchivedAssistantsWithGroupTableAction
      bot={bot}
      onClickRestore={onClickRestore}
      onClickDelete={onClickDelete}
    />
  );

  return (
    <CustomTable<BotWithGroup>
      tableColumns={tableColumns}
      tableData={bots}
      searchFilter={filterBot}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
