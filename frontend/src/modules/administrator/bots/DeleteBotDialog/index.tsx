import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteBot } from "@/orval/administrator-api";
import { Bot, Tenant } from "@/orval/models/administrator-api";

type Props = {
  open: boolean;
  tenant: Tenant;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
};

export const DeleteBotDialog = ({ open, tenant, bot, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteBot(tenant.id, bot.id);

  const deleteBot = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ボットを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ボットの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      <Typography component="span" fontWeight="bold">
        {tenant.name}
      </Typography>
      から
      <Typography component="span" fontWeight="bold">
        {bot.name}
      </Typography>
      を削除してもよろしいですか？
      <br />
      <Typography component="span" fontWeight="bold">
        削除すると元に戻せません。
      </Typography>
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="ボット削除"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={deleteBot}
      isLoading={isMutating}
    />
  );
};
