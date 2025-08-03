import { Stack, Typography } from "@mui/material";

import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateUserPolicy } from "@/orval/backend-api";
import { Bot, UpdateUserPolicyParam, User } from "@/orval/models/backend-api";

import { BotPoliciesTable, BotWithPolicy } from "../BotPoliciesTable";

type Props = {
  user: User;
  bots: Bot[];
  isLoading: boolean;
  refetchUser: () => void;
};

export const UserPolicyManagement = ({ user, bots, refetchUser }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const { trigger: updateUserPolicy } = useUpdateUserPolicy(user.id);
  const userPolicies = user.policies;
  const botIdToUserPolicyMap = new Map(userPolicies.map(policy => [policy.bot_id, policy]));
  const handleUpdateUserPolicy = async (bot: BotWithPolicy) => {
    try {
      const param: UpdateUserPolicyParam = bot.policy
        ? { bot_id: bot.id, action: bot.policy.action }
        : { bot_id: bot.id, delete: true };
      await updateUserPolicy(param);
      refetchUser();
      enqueueSuccessSnackbar({ message: "ポリシーを更新しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ポリシーの更新に失敗しました。" });
    }
  };

  return (
    <>
      <ContentHeader>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h4">アシスタント権限</Typography>
          <RefreshButton onClick={refetchUser} />
        </Stack>
      </ContentHeader>
      <BotPoliciesTable
        botsWithPolicy={bots.map(bot => ({
          ...bot,
          policy: botIdToUserPolicyMap.get(bot.id),
        }))}
        handleUpdateBot={handleUpdateUserPolicy}
      />
    </>
  );
};
