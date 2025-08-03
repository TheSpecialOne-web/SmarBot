import NotificationsIcon from "@mui/icons-material/Notifications";
import { Badge, Button, Typography } from "@mui/material";
import { grey } from "@mui/material/colors";
import { useState } from "react";

import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { useGetNotifications } from "@/orval/backend-api";
import { Notification } from "@/orval/models/backend-api";

import { NotificationDrawer } from "./NotificationDrawer";

// たまに通知の順番がおかしいのでソートする
const sortNotifications = (notifications: Notification[]) => {
  return notifications.sort((a: Notification, b: Notification) => {
    const aDate = new Date(a.start_date);
    const bDate = new Date(b.start_date);
    return bDate.getTime() - aDate.getTime();
  });
};

export const NotificationButtonWithDrawer = () => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState(false);
  const [readNotificationIds, setReadNotificationIds] = useLocalStorage<string[]>(
    "readNotificationIds",
    [],
  );

  const {
    data,
    isValidating: isLoadingNotifications,
    error: getNotificationsError,
  } = useGetNotifications();
  const notifications = data?.notifications || [];

  if (getNotificationsError) {
    enqueueErrorSnackbar({ message: "通知の取得に失敗しました。" });
  }

  const hasUnreadNotifications = notifications.some(
    notification => !readNotificationIds.includes(notification.id),
  );

  const addReadNotification = (id: string) => {
    if (readNotificationIds.includes(id)) return;

    const newReadNotificationIds = [...readNotificationIds, id];
    setReadNotificationIds(newReadNotificationIds);
  };

  return (
    <>
      <Button
        color="inherit"
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          color: grey[900],
          py: 0.5,
        }}
        onClick={() => setIsNotificationDrawerOpen(true)}
      >
        <Badge
          invisible={!hasUnreadNotifications}
          color="error"
          badgeContent=" "
          overlap="circular"
          variant="dot"
        >
          <NotificationsIcon />
        </Badge>
        <Typography fontSize={10}>通知</Typography>
      </Button>

      <NotificationDrawer
        open={isNotificationDrawerOpen}
        onClose={() => setIsNotificationDrawerOpen(false)}
        notifications={sortNotifications(notifications)}
        isLoadingNotifications={isLoadingNotifications}
        readNotificationIds={readNotificationIds}
        addReadNotification={addReadNotification}
      />
    </>
  );
};
