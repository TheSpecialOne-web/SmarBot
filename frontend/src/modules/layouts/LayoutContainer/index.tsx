import { Box } from "@mui/material";
import { ReactNode } from "react";

import { IPBlockedMessage } from "@/components/messages/IPBlockedMessage";
import { ServiceUnavailableMessage } from "@/components/messages/ServiceUnavailableMessage";
import { TOPBAR_HEIGHT } from "@/const";
import { TenantStatus, UserTenant } from "@/orval/models/backend-api";

type Props = {
  tenant?: UserTenant;
  children: ReactNode;
};

export const LayoutContainer = ({ tenant, children }: Props) => {
  return (
    <Box sx={{ pt: `${TOPBAR_HEIGHT}px`, width: "100%" }}>
      {tenant?.ip_blocked ? (
        <Box sx={{ mt: 10 }}>
          <IPBlockedMessage />
        </Box>
      ) : tenant?.status === TenantStatus.suspended ? (
        <Box sx={{ mt: 10 }}>
          <ServiceUnavailableMessage />
        </Box>
      ) : (
        children
      )}
    </Box>
  );
};
