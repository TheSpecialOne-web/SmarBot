import { GroupRole, UserInfo } from "@/orval/models/backend-api";

export const getIsTenantAdmin = (userInfo: UserInfo) => {
  return userInfo.roles.some(role => role === "admin");
};

export const getIsGroupAdmin = ({ userInfo, groupId }: { userInfo: UserInfo; groupId: number }) => {
  if (getIsTenantAdmin(userInfo)) return true;
  return userInfo.groups.find(group => group.id === groupId)?.group_role === GroupRole.group_admin;
};
