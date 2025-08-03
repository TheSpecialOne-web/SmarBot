import { Skeleton, Stack, Typography } from "@mui/material";

import { Spacer } from "@/components/spacers/Spacer";
import { Tenant } from "@/orval/models/backend-api";

type Props = {
  tenant: Tenant;
  isLoadingGetTenant: boolean;
};

export const ForeignRegionManagement = ({ tenant, isLoadingGetTenant }: Props) => {
  const allowForeignRegion = tenant.allow_foreign_region;

  return (
    <Stack>
      <Typography variant="h5">海外リージョンの利用</Typography>
      <Spacer px={8} />
      {isLoadingGetTenant ? (
        <Skeleton variant="rectangular" width={40} height={20} />
      ) : (
        <Typography fontWeight="bold" color={allowForeignRegion ? "primary" : "text.secondary"}>
          {allowForeignRegion ? "有効" : "無効"}
        </Typography>
      )}
      <Spacer px={10} />
      <Stack alignItems="flex-start">
        <Typography variant="caption" color="text.secondary">
          ※
          {allowForeignRegion
            ? "海外リージョンの利用を無効にすると、海外リージョンのモデルを使用できなくなります。"
            : "海外リージョンの利用を有効にすると、海外リージョンのモデルを使用できるようになります。"}
          <br />
          {allowForeignRegion ? "無効" : "有効"}にしたい場合は、運営にお問い合わせください。
        </Typography>
      </Stack>
    </Stack>
  );
};
