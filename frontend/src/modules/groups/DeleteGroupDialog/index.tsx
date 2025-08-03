import { Box, Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteGroup } from "@/orval/backend-api";
import { Group } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  group: Group;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteGroupDialog = ({ open, group, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteGroup(group.id);

  const deleteGroup = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "グループを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "グループの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Box component="span" fontWeight="bold">
        {group.name}
      </Box>
      を削除してもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="グループ削除"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={deleteGroup}
      isLoading={isMutating}
    />
  );
};
