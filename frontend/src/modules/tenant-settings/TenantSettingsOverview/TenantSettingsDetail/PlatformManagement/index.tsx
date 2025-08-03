import { Skeleton, Stack, Typography } from "@mui/material";

import { Spacer } from "@/components/spacers/Spacer";
import { AdditionalPlatform } from "@/orval/models/backend-api/additionalPlatform";

type Props = {
  additionalPlatforms: AdditionalPlatform[];
  isLoadingGetTenant: boolean;
};

export const PlatformManagement = ({ additionalPlatforms, isLoadingGetTenant }: Props) => {
  const hasGcp = additionalPlatforms.includes(AdditionalPlatform.gcp);
  return (
    <Stack>
      <Typography variant="h5">Google Cloudの利用</Typography>
      <Spacer px={8} />
      {isLoadingGetTenant ? (
        <Skeleton variant="rectangular" width={40} height={20} />
      ) : (
        <Typography fontWeight="bold" color={hasGcp ? "primary" : "text.secondary"}>
          {hasGcp ? "有効" : "無効"}
        </Typography>
      )}
      <Spacer px={10} />
      <Stack alignItems="flex-start">
        <Typography variant="caption" color="text.secondary">
          ※
          {hasGcp
            ? "Google Cloudの使用を無効にすると、Google Cloudのモデルを使用できなくなります。"
            : "Google Cloudの使用を有効にすると、Google Cloudのモデルを使用できるようになります。"}
          <br />
          {hasGcp ? "無効" : "有効"}にしたい場合は、運営にお問い合わせください。
        </Typography>
      </Stack>
    </Stack>
  );
};
