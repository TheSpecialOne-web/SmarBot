import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useRestoreBot } from "@/orval/backend-api";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  bot: Bot;
  refetch: () => void;
};

export const RestoreAssistantDialog = ({ open, onClose, bot, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useRestoreBot(bot.id);

  const handleRestore = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "アシスタントを復元しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "アシスタントの復元に失敗しました。" });
    }
  };

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="アシスタントの復元"
      content={
        <Typography>
          <Typography component="span" fontWeight="bold">
            {bot.name}
          </Typography>
          を復元してもよろしいですか？
          <br />
          復元されたアシスタントは、ユーザーに表示されるようになります。
        </Typography>
      }
      buttonText="復元"
      onSubmit={handleRestore}
      isLoading={isMutating}
      color="info"
    />
  );
};
