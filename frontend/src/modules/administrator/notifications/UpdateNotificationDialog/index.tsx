import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { updateNotification } from "@/orval/administrator-api";
import { Notification, UpdateNotificationParam } from "@/orval/models/administrator-api";

import { NotificationForm } from "../NotificationForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  notification: Notification;
};

export const UpdateNotificationDialog = ({ open, onClose, refetch, notification }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const onSubmit = async (params: UpdateNotificationParam) => {
    try {
      await updateNotification(notification.id, params);
      enqueueSuccessSnackbar({ message: "通知を編集しました" });
      refetch();
      onClose();
    } catch (error) {
      enqueueErrorSnackbar({ message: "通知の編集に失敗しました" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="通知を編集" maxWidth="md">
      <NotificationForm onSubmit={onSubmit} onClose={onClose} notification={notification} />
    </CustomDialog>
  );
};
