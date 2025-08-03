import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { createBot } from "@/orval/administrator-api";
import { CreateBotParam, Group, Tenant } from "@/orval/models/administrator-api";

import { CreateBotForm } from "./CreateBotForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  tenant: Tenant;
  groups: Group[];
};

export const CreateBotDialog = ({ open, onClose, refetch, tenant, groups }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const onSubmit = async ({ params, groupId }: { params: CreateBotParam; groupId: number }) => {
    try {
      const paramsForCreate = {
        ...params,
        max_conversation_turns:
          params.max_conversation_turns === 0 ? null : params.max_conversation_turns,
      };
      await createBot(tenant.id, groupId, paramsForCreate);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ボットを作成しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ボットの作成に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="ボット作成">
      <CreateBotForm onSubmit={onSubmit} onClose={onClose} tenant={tenant} groups={groups} />
    </CustomDialog>
  );
};
