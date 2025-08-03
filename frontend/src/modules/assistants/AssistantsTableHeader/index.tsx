import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import AutoStoriesOutlinedIcon from "@mui/icons-material/AutoStoriesOutlined";
import { Link, Stack, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getIsGroupAdmin, getIsTenantAdmin } from "@/libs/permission";

type Props = {
  refetch: () => void;
  groupId?: number;
};

export const AssistantsTableHeader = ({ refetch, groupId }: Props) => {
  const { useAssistantTemplate } = useFlags();
  const { userInfo } = useUserInfo();
  const isGroupAdmin = groupId
    ? getIsGroupAdmin({ userInfo, groupId })
    : getIsTenantAdmin(userInfo);

  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between">
      <Stack direction="row" alignItems="flex-end" gap={1}>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          {`${groupId ? "グループの" : "すべての"}アシスタント`}
        </Typography>
        <Link
          href={
            groupId
              ? `/#/main/groups/${groupId}/assistants/archived`
              : "/#/main/assistants/archived"
          }
          variant="body2"
        >
          アーカイブ済みはこちら
        </Link>
      </Stack>
      <Stack direction="row" gap={2}>
        <RefreshButton onClick={refetch} />
        {isGroupAdmin && (
          <>
            {useAssistantTemplate && (
              <PrimaryButton
                text={<Typography variant="button">テンプレートから作成</Typography>}
                startIcon={<AutoStoriesOutlinedIcon />}
                href={
                  groupId
                    ? `/#/main/groups/${groupId}/assistants/create-from-template`
                    : "/#/main/assistants/create-from-template"
                }
              />
            )}
            <PrimaryButton
              text={<Typography variant="button">新規作成</Typography>}
              startIcon={<AddOutlinedIcon />}
              href={
                groupId
                  ? `/#/main/groups/${groupId}/assistants/create`
                  : "/#/main/assistants/create"
              }
            />
          </>
        )}
      </Stack>
    </Stack>
  );
};
