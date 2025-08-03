import CloseIcon from "@mui/icons-material/Close";
import { Box, Drawer, Skeleton, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { Notification } from "@/orval/models/backend-api";

import { NotificationAccordion } from "./NotificationAccordion";

type Props = {
  open: boolean;
  onClose: () => void;
  notifications: Notification[];
  isLoadingNotifications: boolean;
  readNotificationIds: string[];
  addReadNotification: (id: string) => void;
};

export const NotificationDrawer = ({
  open,
  onClose,
  notifications,
  isLoadingNotifications,
  readNotificationIds,
  addReadNotification,
}: Props) => {
  const [selectedNotificationId, setSelectedNotificationId] = useState<string>();

  const onChange = (id: string, newValue: boolean) => {
    setSelectedNotificationId(newValue ? id : undefined);
    if (newValue) {
      addReadNotification(id);
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: { xs: "100%", sm: "75%", md: "50%" },
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: { xs: "100%", sm: "70%", md: "40%" },
          height: "100%",
          boxSizing: "border-box",
          padding: 2,
          bgcolor: "primaryBackground.main",
        },
      }}
    >
      <Stack gap={2}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h3">通知</Typography>
          <CloseIcon onClick={onClose} sx={{ cursor: "pointer" }} />
        </Stack>
        {isLoadingNotifications ? (
          <Skeleton variant="rectangular" animation="pulse" width="100%" height="100%" />
        ) : notifications.length === 0 ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            height="100%"
            fontWeight="bold"
          >
            通知はありません
          </Box>
        ) : (
          <Box>
            {notifications.map(notification => (
              <NotificationAccordion
                key={notification.id}
                notification={notification}
                expanded={selectedNotificationId === notification.id}
                onChange={onChange}
                isRead={readNotificationIds.includes(notification.id)}
              />
            ))}
          </Box>
        )}
      </Stack>
    </Drawer>
  );
};
