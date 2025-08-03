import { Role, User } from "@/orval/models/backend-api";

export const filterUserByRole = (users: User[], queries: string[]) => {
  if (queries.length === 0) {
    return users.filter(user => user.roles.length === 0);
  }

  if (queries.includes(Role.admin) && !queries.includes(Role.user)) {
    return users.filter(user => user.roles.includes(Role.admin));
  }

  if (queries.includes(Role.user) && !queries.includes(Role.admin)) {
    return users.filter(user => user.roles.includes(Role.user) && !user.roles.includes(Role.admin));
  }

  return users;
};

////////////////////////////////////////////////////////////////////////////////////////////
// administrator
////////////////////////////////////////////////////////////////////////////////////////////

export const filterAssistantTemplatesByStatus = <T extends { is_public: boolean }>(
  assistantTemplates: T[],
  queries: string[],
) => {
  if (queries.length === 0) {
    return [];
  }

  return assistantTemplates.filter(assistantTemplate =>
    queries.includes(assistantTemplate.is_public ? "true" : "false"),
  );
};
