import { Switch, Tooltip, Typography } from "@mui/material";

import { ModelFamilyDetail } from "@/const/modelFamily";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { updateTenantAllowedModelFamily, useGetTenant } from "@/orval/backend-api";
import { AdditionalPlatform, Tenant, UserTenant } from "@/orval/models/backend-api";

import { ModelTables } from "./ModelTables";

const getTooltipMessage = (tenant: Tenant) => {
  const hasGcp = tenant.additional_platforms.includes(AdditionalPlatform.gcp);
  const hasForeignRegion = tenant.allow_foreign_region;

  const disabledList: string[] = [];
  if (!hasGcp) {
    disabledList.push("Google Cloud");
  }
  if (!hasForeignRegion) {
    disabledList.push("海外リージョン");
  }
  return disabledList.length > 0
    ? `${disabledList.join("と")}が無効になっているため追加できません。`
    : "";
};

type Props = {
  tenant: UserTenant;
};

export const ModelManagement = ({ tenant }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const {
    isValidating: isLoadingGetTenant,
    error,
    data: tenantDetail,
    mutate: refetchTenant,
  } = useGetTenant(tenant.id);

  if (error) {
    enqueueErrorSnackbar({ message: "テナントの取得に失敗しました。" });
  }
  const { fetchUserInfo } = useUserInfo();

  const refetch = async () => {
    await Promise.all([refetchTenant(), fetchUserInfo()]);
  };

  const onChange = async (modelFamily: ModelFamilyDetail, enabled: boolean) => {
    try {
      await updateTenantAllowedModelFamily(tenant.id, modelFamily.id, { enabled });
      refetch();
      enqueueSuccessSnackbar({
        message: `${modelFamily.name}を${enabled ? "追加" : "削除"}しました。`,
      });
    } catch (error) {
      const errMsg = getErrorMessage(error);
      enqueueErrorSnackbar({ message: errMsg || `${modelFamily.name}の追加に失敗しました。` });
    }
  };

  const renderActionColumn = (modelFamily: ModelFamilyDetail) => {
    const isAvailable = tenantDetail?.available_model_families.model_families.includes(
      modelFamily.id,
    );
    const isAllowed = tenantDetail?.allowed_model_families.model_families.includes(modelFamily.id);
    const tooltipMessage = tenantDetail && getTooltipMessage(tenantDetail);
    return (
      <Tooltip
        disableInteractive
        title={!isAvailable && <Typography variant="body2">{tooltipMessage}</Typography>}
        placement="top"
      >
        <span>
          <Switch
            checked={isAllowed}
            onChange={event => onChange(modelFamily, event.target.checked)}
            disabled={!isAvailable}
            color={isAllowed ? "primary" : "secondary"}
          />
        </span>
      </Tooltip>
    );
  };

  return <ModelTables isLoading={isLoadingGetTenant} renderActionColumn={renderActionColumn} />;
};
