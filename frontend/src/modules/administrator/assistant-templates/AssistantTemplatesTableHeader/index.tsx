import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import { Stack, Typography } from "@mui/material";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getIsTenantAdmin } from "@/libs/permission";

type Props = {
  refetch: () => void;
};

export const AssistantTemplatesTableHeader = ({ refetch }: Props) => {
  const { userInfo } = useUserInfo();

  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between">
      <Stack direction="row" alignItems="flex-end" gap={1}>
        <Typography variant="h3" sx={{ flexGrow: 1 }}>
          アシスタントテンプレート
        </Typography>
      </Stack>
      <Stack direction="row" gap={2}>
        <RefreshButton onClick={refetch} />
        {getIsTenantAdmin(userInfo) && (
          <PrimaryButton
            text={<Typography variant="button">新規作成</Typography>}
            startIcon={<AddOutlinedIcon />}
            href="/#/administrator/assistant-templates/create"
          />
        )}
      </Stack>
    </Stack>
  );
};
