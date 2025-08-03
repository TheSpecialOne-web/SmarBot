import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { IconButton, Stack } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { formatBotStatus } from "@/libs/bot";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Bot, BotStatus } from "@/orval/models/administrator-api";

const filterAdministratorBot = (bots: Bot[], query: string) => {
  return bots.filter(bot => {
    return filterTest(query, [
      bot.name,
      bot.description,
      bot.index_name || "",
      bot.container_name || "",
      bot.approach,
      bot.search_method || "",
      bot.pdf_parser || "",
    ]);
  });
};

const sortAdministratorBots = (bots: Bot[], order: Order, orderBy: keyof Bot) => {
  const comparator = getComparator<Bot>(order, orderBy);
  return [...bots].sort(comparator);
};

const tableColumns: CustomTableColumn<Bot>[] = [
  {
    key: "id",
    label: "ID",
    align: "left",
    minWidth: 100,
    sortFunction: sortAdministratorBots,
    render: bot => {
      return bot.id;
    },
  },
  {
    key: "name",
    label: "ボット名",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
  {
    key: "description",
    label: "説明",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
  {
    key: "status",
    label: "ステータス",
    align: "left",
    render: bot => formatBotStatus(bot.status),
  },
  {
    key: "approach",
    label: "アプローチ",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
  {
    key: "index_name",
    label: "インデックス",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
  {
    key: "container_name",
    label: "コンテナ名",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
  {
    key: "search_method",
    label: "検索方法",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
  {
    key: "pdf_parser",
    label: "ドキュメント読み取りオプション",
    align: "left",
    sortFunction: sortAdministratorBots,
  },
];

type Props = {
  bots: Bot[];
  onClickUpdateIcon: (bot: Bot) => void;
  onClickDeleteIcon: (bot: Bot) => void;
};

export const BotsTable = ({ bots, onClickUpdateIcon, onClickDeleteIcon }: Props) => {
  const renderActionColumn = (bot: Bot) => {
    return (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButton onClick={() => onClickUpdateIcon(bot)}>
          <EditOutlinedIcon color="primary" />
        </IconButton>
        <IconButton
          onClick={() => onClickDeleteIcon(bot)}
          disabled={bot.status === BotStatus.deleting}
        >
          <DeleteOutlineOutlinedIcon
            color={bot.status === BotStatus.deleting ? "disabled" : "error"}
          />
        </IconButton>
      </Stack>
    );
  };

  return (
    <CustomTable<Bot>
      tableColumns={tableColumns}
      tableData={bots}
      searchFilter={filterAdministratorBot}
      renderActionColumn={renderActionColumn}
    />
  );
};
