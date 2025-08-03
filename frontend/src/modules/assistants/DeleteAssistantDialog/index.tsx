import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteBot } from "@/orval/backend-api";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  bot: Bot;
  refetch: () => void;
};

export const DeleteAssistantDialog = ({ open, onClose, bot, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { isMutating, trigger } = useDeleteBot(bot.id);

  const handleDelete = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "アシスタントを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "アシスタントの削除に失敗しました。" });
    }
  };

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="アシスタントの削除"
      content={
        <Typography>
          <Typography component="span" fontWeight="bold">
            {bot.name}
          </Typography>
          を削除してもよろしいですか？
          <br />
          削除されたアシスタントは、復元できなくなります。
          <br />
          アシスタントに関連するドキュメントも削除されます。
        </Typography>
      }
      buttonText="削除"
      onSubmit={handleDelete}
      isLoading={isMutating}
    />
  );
};
