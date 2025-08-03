import { MenuItem, Select } from "@mui/material";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { isChatGptBot } from "@/libs/bot";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Action, Bot, Policy } from "@/orval/models/backend-api";

export type BotWithPolicy = Bot & { policy: Policy | undefined };

const searchFilter = (bots: BotWithPolicy[], query: string) => {
  return bots.filter(bot => {
    return filterTest(query, [bot.name, bot.description]);
  });
};

const filterBotByPolicy = (items: BotWithPolicy[], queries: string[]) => {
  if (queries.length === 0) {
    return [];
  }

  // "none" タグが含まれている場合、それにマッチするボットを返す
  if (queries.includes("none")) {
    return items.filter(bot => bot.policy === undefined || queries.includes(bot.policy.action));
  }

  // "none" タグが含まれていない場合、残りのタグにマッチするボットを返す
  return items.filter(bot => bot.policy !== undefined && queries.includes(bot.policy.action));
};

const sortBotByNames = (bots: BotWithPolicy[], order: Order, orderBy: keyof BotWithPolicy) => {
  const comparator = getComparator<BotWithPolicy>(order, orderBy);
  return [...bots].sort(comparator);
};

type Props = {
  botsWithPolicy: BotWithPolicy[];
  handleUpdateBot: (bot: BotWithPolicy) => void;
};

export const BotPoliciesTable = ({ botsWithPolicy, handleUpdateBot }: Props) => {
  const tableColumns: CustomTableColumn<BotWithPolicy>[] = [
    {
      key: "name",
      label: "アシスタント名",
      align: "left",
      sortFunction: sortBotByNames,
    },
    {
      key: "policy",
      label: "権限",
      align: "left",
      render: (bot: BotWithPolicy) => {
        const selectedAction = bot.policy?.action ?? "none";
        return (
          <Select
            size="small"
            value={selectedAction}
            onChange={e =>
              handleUpdateBot({
                ...bot,
                policy:
                  e.target.value !== "none"
                    ? {
                        action: e.target.value as Action,
                        bot_id: bot.id,
                      }
                    : undefined,
              })
            }
          >
            <MenuItem value="none">なし</MenuItem>
            <MenuItem value={Action.read}>利用権限</MenuItem>
            {!isChatGptBot(bot) && <MenuItem value={Action.write}>編集権限</MenuItem>}
          </Select>
        );
      },
      columnFilterProps: {
        filterItems: [
          {
            key: Action.write,
            label: "編集権限",
          },
          {
            key: Action.read,
            label: "利用権限",
          },
          {
            key: "none",
            label: "なし",
          },
        ],
        filterFunction: filterBotByPolicy,
      },
    },
  ];

  return (
    <CustomTable<BotWithPolicy>
      tableColumns={tableColumns}
      tableData={botsWithPolicy}
      searchFilter={searchFilter}
      defaultSortProps={{ key: "name", order: "asc" }}
    />
  );
};
