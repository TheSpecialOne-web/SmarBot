import EditIcon from "@mui/icons-material/Edit";
import { Stack, Typography } from "@mui/material";
import dayjs from "dayjs";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { Spacer } from "@/components/spacers/Spacer";
import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { modelNames } from "@/const/modelFamily";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { BotWithGroup } from "@/orval/models/backend-api";

import { AssistantsTableApproachColumn } from "../AssistantsTableApproachColumn";
import { AssistantsTableNameColumn } from "../AssistantsTableNameColumn";
import { AssistantsWithGroupTableAction } from "./AssistantsWithGroupTableAction";

const sortBots = (bots: BotWithGroup[], order: Order, orderBy: keyof BotWithGroup) => {
  const comparator = getComparator<BotWithGroup>(order, orderBy);
  return [...bots].sort(comparator);
};

const filterBot = (bots: BotWithGroup[], query: string) => {
  return bots.filter(bot => {
    return filterTest(query, [bot.name, bot.description]);
  });
};

const getTableColumns = (
  onClickUpdateBotGroup: (bot: BotWithGroup) => void,
  isTenantAdmin: boolean,
): CustomTableColumn<BotWithGroup>[] => [
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
    render: bot => (
      <Stack direction="row" alignItems="center">
        <Typography variant="subtitle2">{bot.group_name}</Typography>
        <Spacer px={4} horizontal />
        <IconButtonWithTooltip
          tooltipTitle={
            !isTenantAdmin ? "所属グループの変更には組織管理者権限が必要です" : "所属グループを変更"
          }
          icon={<EditIcon sx={{ fontSize: 18 }} />}
          disabled={!isTenantAdmin}
          onClick={() => onClickUpdateBotGroup(bot)}
        />
      </Stack>
    ),
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
  bots: BotWithGroup[];
  onClickStartChat: (bot: BotWithGroup) => void;
  onClickArchive: (bot: BotWithGroup) => void;
  onClickUpdateBotGroup: (bot: BotWithGroup) => void;
  isTenantAdmin: boolean;
};

export const AssistantsWithGroupTable = ({
  bots,
  onClickStartChat,
  onClickArchive,
  onClickUpdateBotGroup,
  isTenantAdmin,
}: Props) => {
  const renderActionColumn = (bot: BotWithGroup) => {
    return (
      <AssistantsWithGroupTableAction
        onClickStartChat={() => onClickStartChat(bot)}
        onClickArchive={() => onClickArchive(bot)}
        groupId={bot.group_id}
      />
    );
  };

  return (
    <CustomTable<BotWithGroup>
      tableColumns={getTableColumns(onClickUpdateBotGroup, isTenantAdmin)}
      tableData={bots}
      searchFilter={filterBot}
      defaultSortProps={{ key: "name", order: "asc" }}
      renderActionColumn={renderActionColumn}
    />
  );
};
