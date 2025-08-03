import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateGroup } from "@/orval/backend-api";
import { CreateGroupParam, User } from "@/orval/models/backend-api";

import { CreateGroupForm } from "./CreateGroupForm";

type Props = {
  users: User[];
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreateGroupDialog = ({ users, open, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: createGroup } = useCreateGroup();

  const onSubmit = async (params: CreateGroupParam) => {
    try {
      await createGroup(params);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "グループを作成しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "グループの作成に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="グループ作成">
      <CreateGroupForm users={users} onSubmit={onSubmit} onClose={onClose} />
    </CustomDialog>
  );
};
