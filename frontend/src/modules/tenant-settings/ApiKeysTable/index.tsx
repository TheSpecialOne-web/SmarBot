import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { Box, Link, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import { useFlags } from "launchdarkly-react-client-sdk";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { BotProfile } from "@/modules/tenant-settings/BotProfile";
import { ApiKey } from "@/orval/models/backend-api";
import { formatDate } from "@/utils/formatDate";

const filterApiKey = (apiKeys: ApiKey[], query: string) => {
  return apiKeys.filter(apiKey => {
    return filterTest(query, [
      apiKey.name,
      apiKey.bot.name,
      apiKey?.expires_at ? formatDate(apiKey.expires_at) : "",
    ]);
  });
};

const isExpired = (expires_at: string) => {
  return dayjs(expires_at).isBefore(dayjs());
};

const sortApiKeys = (apiKeys: ApiKey[], order: Order, orderBy: keyof ApiKey) => {
  const comparator = getComparator<ApiKey>(order, orderBy);
  return [...apiKeys].sort(comparator);
};

// 深い階層のpropertyでsort
const sortBot = (apiKeys: ApiKey[], order: Order) => {
  const apiKeysWithBotName = apiKeys.map(({ bot, ...rest }) => ({
    botName: bot.name,
    bot,
    ...rest,
  }));
  const comparator = getComparator<ApiKey & { botName: string }>(order, "botName");

  return [...apiKeysWithBotName]
    .sort(comparator)
    .map(({ botName: _botName, ...rest }) => rest as ApiKey);
};

type Props = {
  apiKeys: ApiKey[];
  selectedRowIds: string[];
  handleSelectRow: (ids: string[]) => void;
  onClickApiKeyName: (apiKey: ApiKey) => void;
};

const noApiKeyContent = (
  <Box
    sx={{
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
    }}
  >
    <Typography variant="body2">
      右上の「追加」ボタンをクリックしてAPIキーを追加してください。
    </Typography>
  </Box>
);

export const ApiKeysTable = ({
  apiKeys,
  selectedRowIds,
  handleSelectRow,
  onClickApiKeyName,
}: Props) => {
  const { embedChatUi } = useFlags();

  const tableColumns: CustomTableColumn<ApiKey>[] = [
    {
      key: "name",
      label: "名前",
      align: "left",
      sortFunction: sortApiKeys,
      render: apiKey =>
        embedChatUi ? (
          <Link
            onClick={() => onClickApiKeyName(apiKey)}
            sx={{
              cursor: "pointer",
            }}
          >
            {apiKey.name}
          </Link>
        ) : (
          apiKey.name
        ),
    },
    {
      key: "bot",
      label: "アシスタント",
      align: "left",
      sortFunction: sortBot,
      render: apiKey => <BotProfile bot={apiKey.bot} />,
    },
    {
      key: "expires_at",
      label: "有効期限",
      align: "left",
      render: apiKey => {
        if (!apiKey.expires_at) return "無期限";
        if (!isExpired(apiKey.expires_at)) {
          return <Typography>{formatDate(apiKey.expires_at)}</Typography>;
        }
        // 期限切れの場合
        return (
          <Stack direction="row" alignItems="center" gap={1}>
            <ErrorOutlineIcon color="error" />
            <Typography color={"error"}>{formatDate(apiKey.expires_at)}</Typography>
          </Stack>
        );
      },
      sortFunction: sortApiKeys,
    },
  ];

  return (
    <CustomTable<ApiKey>
      tableColumns={tableColumns}
      tableData={apiKeys}
      noDataContent={noApiKeyContent}
      searchFilter={filterApiKey}
      checkboxProps={{
        selectedRowIds: selectedRowIds,
        setSelectedRowIds: handleSelectRow,
      }}
    />
  );
};
