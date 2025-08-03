import { TenantStatus } from "@/orval/models/administrator-api";

export const displayTenantStatus = (status: TenantStatus) => {
  switch (status) {
    case TenantStatus.trial:
      return "トライアル中";
    case TenantStatus.suspended:
      return "利用停止中";
    case TenantStatus.subscribed:
      return "本契約中";
  }
};
