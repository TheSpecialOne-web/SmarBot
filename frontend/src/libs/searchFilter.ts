import { Group, GroupUser, User } from "@/orval/models/backend-api";

// 例: ぽ → ぽ (消そうとしたらわかるけど、これらは違う文字)
// https://zenn.dev/hacobell_dev/articles/68ccc92bffd6cc
const convertToNFC = (str: string) => {
  return str.normalize("NFC");
};

export const filterTest = (query: string, targets: string[]) => {
  const search = convertToNFC(query.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&"));
  const regex = new RegExp(search, "i");
  return targets.some(target => {
    const normalizedTarget = convertToNFC(target);
    return regex.test(normalizedTarget);
  });
};

export const filterGroup = (groups: Group[], query: string) => {
  return groups.filter(group => {
    return filterTest(query, [group.name]);
  });
};

export const filterGroupUser = (users: GroupUser[], query: string) => {
  return users.filter(user => {
    return filterTest(query, [user.name, user.email]);
  });
};

export const filterUser = (users: User[], query: string) => {
  return users.filter(user => {
    return filterTest(query, [user.name, user.email]);
  });
};
