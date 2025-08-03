import { Bot, UserInfo } from "@/orval/models/backend-api";

import { getIsTenantAdmin } from "./permission";

export const getHasWritePolicy = (bot: Bot, userInfo: UserInfo) => {
  if (getIsTenantAdmin(userInfo)) return true;
  return userInfo.policies?.some(
    policy => (policy.action === "write" || policy.action === "all") && policy.bot_id === bot.id,
  );
};
