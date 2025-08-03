import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateBot } from "@/orval/administrator-api";
import { Bot, Tenant, UpdateBotParam } from "@/orval/models/administrator-api";

import { UpdateBotForm } from "./UpdateBotForm";

type Props = {
  open: boolean;
  tenant: Tenant;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateBotDialog = ({ open, tenant, bot, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger } = useUpdateBot(tenant.id, bot.id);

  const updateBot = async (param: UpdateBotParam) => {
    try {
      const paramsForUpdate = {
        ...param,
        max_conversation_turns:
          param.max_conversation_turns === 0 ? null : param.max_conversation_turns,
      };
      await trigger(paramsForUpdate);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ボットを更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ボットの更新に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="ボット編集">
      <UpdateBotForm tenant={tenant} bot={bot} handleUpdateBot={updateBot} onClose={onClose} />
    </CustomDialog>
  );
};
