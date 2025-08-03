import { GroupRole } from "@/orval/models/backend-api";

export const groupRoleToJapanese = (groupRole: GroupRole) => {
  switch (groupRole) {
    case GroupRole.group_admin:
      return "グループ管理者";
    case GroupRole.group_editor:
      return "アシスタント編集者";
    case GroupRole.group_viewer:
      return "アシスタント閲覧者";
  }
};
