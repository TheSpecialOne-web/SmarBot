import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteUsersFromGroup } from "@/orval/backend-api";
import { GroupUser } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  groupId: number;
  groupUser: GroupUser;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteGroupUserDialog = ({ open, groupId, groupUser, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteUsersFromGroup(groupId);

  const deleteUser = async () => {
    try {
      await trigger({ user_ids: [groupUser.id] });
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ユーザーをグループから削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "グループからユーザーの削除に失敗しました。" });
    }
  };

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="ユーザー削除"
      content={<Typography>{groupUser.name}をグループから削除しますか？</Typography>}
      buttonText="削除"
      onSubmit={deleteUser}
      isLoading={isMutating}
    />
  );
};
