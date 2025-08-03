import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateTenant } from "@/orval/administrator-api";
import { Tenant, UpdateTenantParam } from "@/orval/models/administrator-api";

import { UsageLimitForm } from "./Form";

type Props = {
  tenant: Tenant;
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateUsageLimitDialog = ({ tenant, open, onClose, refetch }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();

  const { trigger } = useUpdateTenant(tenant.id);

  const handleUpdateTenant = async (params: UpdateTenantParam) => {
    try {
      await trigger(params);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "テナントを更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "不明なエラーが発生しました。" });
    }
  };

  return (
    <CustomDialog open={open} title="利用枠編集" maxWidth="md" onClose={onClose}>
      <CustomDialogContent>
        <UsageLimitForm tenant={tenant} handleUpdateTenant={handleUpdateTenant} />
      </CustomDialogContent>
    </CustomDialog>
  );
};
