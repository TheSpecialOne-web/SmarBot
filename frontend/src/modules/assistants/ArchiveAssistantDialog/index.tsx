import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useArchiveBot } from "@/orval/backend-api";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  bot: Bot;
  refetch: () => void;
};

export const ArchiveAssistantDialog = ({ open, onClose, bot, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useArchiveBot(bot.id);

  const handleArchive = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "アシスタントをアーカイブしました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "アシスタントのアーカイブに失敗しました。" });
    }
  };

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="アシスタントのアーカイブ"
      content={
        <Typography>
          <Typography component="span" fontWeight="bold">
            {bot.name}
          </Typography>
          をアーカイブしてもよろしいですか？
          <br />
          アーカイブされたアシスタントは、ユーザーに表示されなくなります。
          <br />
          アーカイブされたアシスタントは、後から復元することができます。
        </Typography>
      }
      buttonText="アーカイブ"
      onSubmit={handleArchive}
      isLoading={isMutating}
    />
  );
};
