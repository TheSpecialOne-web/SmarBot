import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteUser } from "@/orval/backend-api";
import { User } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  user: User;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteUserDialog = ({ open, user, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteUser(user.id);

  const deleteUser = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ユーザーを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ユーザーの削除に失敗しました。" });
    }
  };

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="ユーザー削除"
      content={
        <Typography>
          <Typography component="span" fontWeight="bold">
            {user.name} ({user.email})
          </Typography>
          <br />
          を削除してもよろしいですか？
        </Typography>
      }
      buttonText="削除"
      onSubmit={deleteUser}
      isLoading={isMutating}
    />
  );
};
