import { useState } from "react";
import { useAsyncFn } from "react-use";

import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { getTenantGuideline, useGetTenant, useGetTenantGuidelines } from "@/orval/backend-api";
import { Guideline, GuidelineDetail, UserTenant } from "@/orval/models/backend-api";

import { CreateTenantGuidelineDialog } from "./CreateTenantGuidelineDialog";
import { DeleteTenantGuidelineDialog } from "./DeleteTenantGuidelineDialog";
import { PreviewTenantGuidelineDrawer } from "./PreviewTenantGuidelineDrawer";
import { TenantGuidelines } from "./TenantGuidelines";
import { TenantSettingsDetail } from "./TenantSettingsDetail";

type Props = {
  tenant: UserTenant;
};

export const TenantSettingsOverview = ({ tenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const { fetchUserInfo } = useUserInfo();
  const {
    isValidating: isLoadingGetTenant,
    error: getTenantError,
    data: tenantDetail,
    mutate: refetchTenant,
  } = useGetTenant(tenant.id);
  if (getTenantError) {
    const errMsg = getErrorMessage(getTenantError);
    enqueueErrorSnackbar({
      message: errMsg || "組織の情報の取得に失敗しました",
    });
  }

  const {
    data: getGuidelinesData,
    isValidating: isLoadingGetGuidelines,
    error: getGuidelinesError,
    mutate: refetchGuidelines,
  } = useGetTenantGuidelines(tenant.id);
  if (getGuidelinesError) {
    const errMsg = getErrorMessage(getGuidelinesError);
    enqueueErrorSnackbar({
      message: errMsg || "ガイドラインの取得に失敗しました",
    });
  }
  const guidelines = getGuidelinesData?.guidelines ?? [];

  const [guidelineToPreview, setGuidelineToPreview] = useState<GuidelineDetail | null>();
  const [guidelineToDelete, setGuidelineToDelete] = useState<Guideline | null>();

  const {
    isOpen: isOpenCreateGuidelineDialog,
    open: openCreateGuidelineDialog,
    close: closeCreateGuidelineDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenDeleteGuidelineDialog,
    open: openDeleteGuidelineDialog,
    close: closeDeleteGuidelineDialog,
  } = useDisclosure({ onClose: () => setGuidelineToDelete(null) });

  const {
    isOpen: isOpenPreviewGuidelineDrawer,
    open: openPreviewGuidelineDrawer,
    close: closePreviewGuidelineDrawer,
  } = useDisclosure({ onClose: () => setGuidelineToPreview(null) });

  const [
    { loading: isLoadingPreviewGuideline, error: previewGuidelineError },
    handleClickGuideline,
  ] = useAsyncFn(async (guideline: Guideline) => {
    try {
      const guidelineDetail = await getTenantGuideline(tenant.id, guideline.id);
      setGuidelineToPreview(guidelineDetail);
      openPreviewGuidelineDrawer();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ガイドラインの表示に失敗しました。" });
    }
  });

  const handleOpenDeleteGuidelineDialog = (guideline: Guideline) => {
    openDeleteGuidelineDialog();
    setGuidelineToDelete(guideline);
  };

  const refetch = () => {
    refetchTenant();
    fetchUserInfo();
    refetchGuidelines();
  };

  return (
    <>
      {tenantDetail && (
        <TenantSettingsDetail
          tenant={tenantDetail}
          refetch={refetch}
          isLoadingGetTenant={isLoadingGetTenant}
        />
      )}

      <Spacer px={16} />

      <TenantGuidelines
        guidelines={guidelines}
        isLoadingGetGuidelines={isLoadingGetGuidelines}
        refetchGuidelines={refetchGuidelines}
        onOpenCreateGuidelineDialog={openCreateGuidelineDialog}
        onOpenDeleteGuidelineDialog={handleOpenDeleteGuidelineDialog}
        onClickGuideline={handleClickGuideline}
      />

      {guidelineToPreview && (
        <PreviewTenantGuidelineDrawer
          open={isOpenPreviewGuidelineDrawer}
          onClose={closePreviewGuidelineDrawer}
          guidelineDetail={guidelineToPreview}
          loading={isLoadingPreviewGuideline}
          error={Boolean(previewGuidelineError)}
        />
      )}

      <CreateTenantGuidelineDialog
        open={isOpenCreateGuidelineDialog}
        onClose={closeCreateGuidelineDialog}
        refetch={refetch}
      />

      {guidelineToDelete && (
        <DeleteTenantGuidelineDialog
          open={isOpenDeleteGuidelineDialog}
          onClose={closeDeleteGuidelineDialog}
          refetch={refetch}
          guideline={guidelineToDelete}
        />
      )}
    </>
  );
};
