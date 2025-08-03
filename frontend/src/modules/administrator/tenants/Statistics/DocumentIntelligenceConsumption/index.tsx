import { LinearProgress, Paper, Skeleton, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import { FormProvider, useForm } from "react-hook-form";

import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useGetTenantDocumentIntelligencePageCount } from "@/orval/administrator-api";
import { Tenant } from "@/orval/models/administrator-api";
import { numberToString } from "@/utils/formatNumber";
import { showOldPricingPlan } from "@/utils/isOldPricingPlan";

import { SelectDateForm, SelectDateFormParams } from "../SelectDateForm";

type Props = {
  tenant: Tenant;
  isLoadingGetTenant: boolean;
};

export const DocumentIntelligenceConsumption = ({ tenant, isLoadingGetTenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const useFormMethods = useForm<SelectDateFormParams>({
    defaultValues: {
      year: new Date().getFullYear(),
      month: new Date().getMonth() + 1,
    },
  });
  const { watch } = useFormMethods;

  const {
    data: documentIntelligencePageCountData,
    isValidating: isLoadingGetTenantDocumentIntelligencePageCount,
    mutate: fetchTenantDocumentIntelligencePageCount,
    error: getTenantDocumentIntelligencePageCountError,
  } = useGetTenantDocumentIntelligencePageCount(tenant.id, {
    start_date_time: dayjs()
      .year(watch("year"))
      .month(watch("month") - 1)
      .startOf("month")
      .toISOString(),
    end_date_time: dayjs().year(watch("year")).month(watch("month")).startOf("month").toISOString(),
  });

  const isOldPricingPlan = showOldPricingPlan(dayjs().year(watch("year")).month(watch("month")));

  const documentIntelligencePageCount = isOldPricingPlan
    ? documentIntelligencePageCountData?.count ?? 0
    : 0;

  if (getTenantDocumentIntelligencePageCountError) {
    const errMsg = getErrorMessage(getTenantDocumentIntelligencePageCountError);
    enqueueErrorSnackbar({ message: errMsg || "高精度表読み取り+OCR処理数の取得に失敗しました。" });
  }

  const documentIntelligencePageLimit = tenant.usage_limit.document_intelligence_page;

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h3">高精度表読み取り+OCR処理数</Typography>
          <RefreshButton onClick={fetchTenantDocumentIntelligencePageCount} />
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          p: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Stack gap={3}>
          <FormProvider {...useFormMethods}>
            <SelectDateForm disabled={isLoadingGetTenantDocumentIntelligencePageCount} />
          </FormProvider>
          <Stack gap={1}>
            {isLoadingGetTenant || isLoadingGetTenantDocumentIntelligencePageCount ? (
              <>
                <Skeleton animation="pulse" variant="text" width={100} height={24} />
                <Skeleton animation="pulse" variant="text" width="100%" height={4} />
              </>
            ) : (
              <>
                <Typography fontWeight="bold">
                  {numberToString(documentIntelligencePageCount)} /{" "}
                  {numberToString(documentIntelligencePageLimit)}{" "}
                  <Typography component="span" fontSize="small" fontWeight="bold">
                    ページ
                  </Typography>
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(documentIntelligencePageCount / documentIntelligencePageLimit) * 100}
                />
                {!isOldPricingPlan && (
                  <Typography component="span" fontSize="small" fontWeight="bold">
                    ※2024年12月より、「高精度表読み取り+OCR処理数」は「消費トークン数」に統合されます。
                  </Typography>
                )}
              </>
            )}
          </Stack>
        </Stack>
      </Paper>
    </>
  );
};
