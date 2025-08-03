import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useArchiveNotification } from "@/orval/administrator-api";
import { Notification } from "@/orval/models/administrator-api";

type Props = {
  open: boolean;
  notification: Notification;
  onClose: () => void;
  refetch: () => void;
};

export const ArchiveNotificationDialog = ({ open, notification, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useArchiveNotification(notification.id);

  const archiveNotification = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "通知をアーカイブしました。" });
    } catch (e) {
      enqueueErrorSnackbar({ message: "通知のアーカイブに失敗しました。" });
    }
  };

  const archiveDialogContents = (
    <Typography>
      <Typography component="span" fontWeight="bold">
        {notification.title}
      </Typography>
      をアーカイブしてもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="通知アーカイブ"
      content={archiveDialogContents}
      buttonText="アーカイブ"
      onSubmit={archiveNotification}
      isLoading={isMutating}
    />
  );
};
