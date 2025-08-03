import { Box, Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDeleteBotTemplate } from "@/orval/administrator-api";
import { BotTemplate } from "@/orval/models/administrator-api";

type Props = {
  open: boolean;
  bot: BotTemplate;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteAssistantTemplateDialog = ({ open, bot, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteBotTemplate(bot.id);

  const deleteGroup = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "アシスタントテンプレートを削除しました。" });
    } catch (e) {
      enqueueErrorSnackbar({ message: "アシスタントテンプレートの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Box component="span" fontWeight="bold">
        {bot.name}
      </Box>
      を削除してもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="アシスタントテンプレート削除"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={deleteGroup}
      isLoading={isMutating}
    />
  );
};
