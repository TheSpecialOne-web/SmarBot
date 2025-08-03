import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { IconButton, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";

import { CustomTable, CustomTableColumn, Order } from "@/components/tables/CustomTable";
import { filterTest } from "@/libs/searchFilter";
import { getComparator } from "@/libs/sort";
import { Notification, NotificationStatus, RecipientType } from "@/orval/models/administrator-api";

const TABLE_MAX_STRING_LENGTH = 20;

const filterNotifications = (notifications: Notification[], query: string) => {
  return notifications.filter(notification => {
    return filterTest(query, [notification.title, notification.content]);
  });
};

const sortNotifications = (
  notifications: Notification[],
  order: Order,
  orderBy: keyof Notification,
) => {
  const comparator = getComparator<Notification>(order, orderBy);
  return [...notifications].sort(comparator);
};

const filterNotificationsByStatus = (notifications: Notification[], queries: string[]) => {
  if (queries.length === 0) {
    return [];
  }

  return notifications.filter(notification => queries.includes(notification.status || ""));
};

const filterNotificationsByRecipientType = (notifications: Notification[], queries: string[]) => {
  if (queries.length === 0) {
    return [];
  }

  return notifications.filter(notification => queries.includes(notification.recipient_type));
};

const tableColumns: CustomTableColumn<Notification>[] = [
  {
    key: "title",
    label: "タイトル",
    align: "left",
    sortFunction: sortNotifications,
    render: notification => {
      return (
        <Typography sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {notification.title.length > TABLE_MAX_STRING_LENGTH
            ? `${notification.title.slice(0, TABLE_MAX_STRING_LENGTH - 1)}...`
            : notification.title}
        </Typography>
      );
    },
  },
  {
    key: "content",
    label: "内容",
    align: "left",
    sortFunction: sortNotifications,
    render: notification => {
      return (
        <Typography sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {notification.content.length > TABLE_MAX_STRING_LENGTH
            ? `${notification.content.slice(0, TABLE_MAX_STRING_LENGTH - 1)}...`
            : notification.content}
        </Typography>
      );
    },
  },
  {
    key: "status",
    label: "ステータス",
    align: "left",
    render: notification => {
      return (
        <Typography>
          {notification.status === NotificationStatus.pending
            ? "未送信"
            : notification.status === NotificationStatus.active
            ? "配信中"
            : "配信終了"}
        </Typography>
      );
    },
    columnFilterProps: {
      filterFunction: filterNotificationsByStatus,
      filterItems: [
        { key: NotificationStatus.pending, label: "未送信" },
        { key: NotificationStatus.active, label: "配信中" },
        { key: NotificationStatus.finished, label: "配信終了" },
      ],
    },
  },
  {
    key: "recipient_type",
    label: "受信者",
    align: "left",
    render: notification => {
      return (
        <Typography>
          {notification.recipient_type === RecipientType.user ? "ユーザー向け" : "組織管理者向け"}
        </Typography>
      );
    },
    columnFilterProps: {
      filterFunction: filterNotificationsByRecipientType,
      filterItems: [
        { key: RecipientType.user, label: "ユーザー向け" },
        { key: RecipientType.admin, label: "組織管理者向け" },
      ],
    },
  },
  {
    key: "start_date",
    label: "配信開始日",
    align: "left",
    sortFunction: sortNotifications,
    render: notification => {
      return <Typography>{dayjs(notification.start_date).format("YYYY/MM/DD")}</Typography>;
    },
  },
  {
    key: "end_date",
    label: "配信終了日",
    align: "left",
    sortFunction: sortNotifications,
    render: notification => {
      return <Typography>{dayjs(notification.end_date).format("YYYY/MM/DD")}</Typography>;
    },
  },
];

type Props = {
  notifications: Notification[];
  onClickUpdateIcon: (notification: Notification) => void;
  onClickArchiveIcon: (notification: Notification) => void;
};

export const NotificationsTable = ({
  notifications,
  onClickUpdateIcon,
  onClickArchiveIcon,
}: Props) => {
  const renderActionColumn = (notification: Notification) => {
    return (
      <Stack direction="row" gap={1} justifyContent="right">
        <IconButton onClick={() => onClickUpdateIcon(notification)}>
          <EditOutlinedIcon color="primary" />
        </IconButton>
        <IconButton onClick={() => onClickArchiveIcon(notification)}>
          <ArchiveOutlinedIcon color="error" />
        </IconButton>
      </Stack>
    );
  };

  return (
    <CustomTable<Notification>
      tableColumns={tableColumns}
      tableData={notifications}
      searchFilter={filterNotifications}
      renderActionColumn={renderActionColumn}
      defaultSortProps={{ key: "start_date", order: "desc" }}
    />
  );
};
