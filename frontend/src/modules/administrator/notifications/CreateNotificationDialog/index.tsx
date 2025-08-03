import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { createNotification } from "@/orval/administrator-api";
import { CreateNotificationParam } from "@/orval/models/administrator-api";

import { NotificationForm } from "../NotificationForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreateNotificationDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();

  const onSubmit = async (params: CreateNotificationParam) => {
    try {
      await createNotification(params);
      enqueueSuccessSnackbar({ message: "通知を作成しました" });
      refetch();
      onClose();
    } catch (error) {
      enqueueErrorSnackbar({ message: "通知の作成に失敗しました" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="通知を作成" maxWidth="md">
      <NotificationForm onSubmit={onSubmit} onClose={onClose} notification={null} />
    </CustomDialog>
  );
};
