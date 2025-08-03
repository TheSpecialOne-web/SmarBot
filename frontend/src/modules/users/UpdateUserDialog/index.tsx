import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { useCreateUserRole, useDeleteUserRole, useUpdateUser } from "@/orval/backend-api";
import { User } from "@/orval/models/backend-api";

import { UpdateUserForm, UserInfoParam } from "./UpdateUserForm";

type Props = {
  open: boolean;
  user: User;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateUserDialog = ({ open, user, onClose, refetch }: Props) => {
  const { userInfo } = useUserInfo();
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const { trigger: updateUser } = useUpdateUser(user.id);

  const { trigger: createAdminRole } = useCreateUserRole(user.id);
  const { trigger: deleteAdminRole } = useDeleteUserRole(user.id, "admin");

  const handleSubmitUserInfo = async (param: UserInfoParam) => {
    try {
      await updateUser(param);
      if (param.role === "user") {
        await deleteAdminRole();
      } else {
        await createAdminRole({ roles: ["admin"] });
      }
      refetch();
      enqueueSuccessSnackbar({ message: "ユーザー情報を更新しました。" });
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ユーザーの更新に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} maxWidth="md" title="ユーザー情報編集">
      <UpdateUserForm
        user={user}
        onSubmit={handleSubmitUserInfo}
        onClose={onClose}
        canUpdateRole={userInfo.id !== user.id}
      />
    </CustomDialog>
  );
};
