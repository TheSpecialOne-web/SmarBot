import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateGroup } from "@/orval/backend-api";
import { Group, UpdateGroupParam } from "@/orval/models/backend-api";

import { UpdateGroupForm } from "./UpdateGroupForm";

type Props = {
  open: boolean;
  group: Group;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateGroupDialog = ({ open, group, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger } = useUpdateGroup(group.id);

  const updateGroup = async (param: UpdateGroupParam) => {
    try {
      await trigger(param);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "グループを更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "グループの更新に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="グループ編集">
      <UpdateGroupForm group={group} onSubmit={updateGroup} onClose={onClose} />
    </CustomDialog>
  );
};
