import { Skeleton, Stack, Switch, Typography } from "@mui/material";

import { SENSITIVE_CONTENTS } from "@/const";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateTenantSensitiveMasking } from "@/orval/backend-api";
import { Tenant } from "@/orval/models/backend-api";

type Props = {
  tenant: Tenant;
  refetch: () => void;
  isLoadingGetTenant: boolean;
};

export const PersonalInfoManagement = ({ tenant, refetch, isLoadingGetTenant }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const isSensitiveMasked = tenant.is_sensitive_masked;

  const { isMutating: isLoading, trigger: updateTenantSensitiveMasking } =
    useUpdateTenantSensitiveMasking(tenant.id);

  const handleSwitch = async () => {
    try {
      await updateTenantSensitiveMasking({
        is_sensitive_masked: !isSensitiveMasked,
      });
      enqueueSuccessSnackbar({ message: "個人情報検出を更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "個人情報検出の更新に失敗しました。",
      });
    }
    refetch();
  };

  return (
    <Stack>
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Typography variant="h5">個人情報の検出</Typography>
        {isLoadingGetTenant ? (
          <Skeleton variant="rectangular" width={40} height={20} />
        ) : (
          <Switch checked={isSensitiveMasked} onChange={handleSwitch} disabled={isLoading} />
        )}
      </Stack>
      <Typography variant="subtitle2">
        ユーザーの入力に以下の種類の個人情報が含まれている場合に質問を送信することができなくなります。
        <br />
        {Object.entries(SENSITIVE_CONTENTS).map(([key, value]) => (
          <span key={key}>
            ・{value}
            <br />
          </span>
        ))}
        ※個人情報検出機能は、100%検知することを保証するものではありません。
      </Typography>
    </Stack>
  );
};
