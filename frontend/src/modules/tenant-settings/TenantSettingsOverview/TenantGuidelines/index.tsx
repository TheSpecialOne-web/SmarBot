import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Stack, Typography } from "@mui/material";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { Guideline } from "@/orval/models/backend-api";

import { TenantGuidelinesTable } from "./TenantGuidelinesTable";

type Props = {
  guidelines: Guideline[];
  isLoadingGetGuidelines: boolean;
  refetchGuidelines: () => void;
  onOpenCreateGuidelineDialog: () => void;
  onOpenDeleteGuidelineDialog: (guideline: Guideline) => void;
  onClickGuideline: (guideline: Guideline) => void;
};

export const TenantGuidelines = ({
  guidelines,
  isLoadingGetGuidelines,
  refetchGuidelines,
  onOpenCreateGuidelineDialog,
  onOpenDeleteGuidelineDialog,
  onClickGuideline,
}: Props) => {
  if (isLoadingGetGuidelines) {
    return <CustomTableSkeleton />;
  }
  return (
    <>
      <ContentHeader>
        <Stack direction="row" justifyContent="space-between">
          <Stack direction="row" alignItems="center" gap={1}>
            <Typography variant="h3">ガイドライン</Typography>
            <IconButtonWithTooltip
              tooltipTitle="ガイドラインを登録するとチャット画面から全てのユーザーが確認できます"
              color="primary"
              icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
              iconButtonSx={{ p: 0.5 }}
            />
          </Stack>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchGuidelines} />
            <PrimaryButton
              text={<Typography variant="button">新規作成</Typography>}
              startIcon={<AddOutlinedIcon />}
              onClick={onOpenCreateGuidelineDialog}
            />
          </Stack>
        </Stack>
      </ContentHeader>
      <TenantGuidelinesTable
        guidelines={guidelines}
        onClickDeleteIcon={onOpenDeleteGuidelineDialog}
        onClickGuideline={onClickGuideline}
      />
    </>
  );
};
